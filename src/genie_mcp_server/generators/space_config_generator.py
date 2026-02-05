"""LLM-powered Genie space configuration generator."""

import json
import re
from typing import Any, Optional

import httpx
from databricks.sdk import WorkspaceClient

from genie_mcp_server.generators.prompts import build_config_generation_prompt
from genie_mcp_server.models.space import LLMResponse
from genie_mcp_server.utils.error_handling import LLMError


class GenieConfigGenerator:
    """Generates Genie space configurations using LLM."""

    def __init__(
        self,
        workspace_client: WorkspaceClient,
        serving_endpoint_name: str = "databricks-dbrx-instruct",
        max_retries: int = 3,
    ):
        """Initialize the config generator.

        Args:
            workspace_client: Authenticated Databricks workspace client
            serving_endpoint_name: Name of the serving endpoint to use
            max_retries: Maximum number of retry attempts
        """
        self.client = workspace_client
        self.serving_endpoint_name = serving_endpoint_name
        self.max_retries = max_retries

    def generate_config(
        self,
        requirements: str,
        catalog_name: str,
        warehouse_id: str,
        table_metadata: Optional[str] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a Genie space configuration from requirements.

        Args:
            requirements: Natural language description of desired space
            catalog_name: Unity Catalog name
            warehouse_id: SQL warehouse ID
            table_metadata: Optional table metadata context
            temperature: LLM temperature (0-1, lower = more deterministic)

        Returns:
            LLMResponse with generated configuration and reasoning

        Raises:
            LLMError: If generation fails
        """
        # Build prompt
        prompt = build_config_generation_prompt(
            requirements=requirements,
            catalog_name=catalog_name,
            warehouse_id=warehouse_id,
            table_metadata=table_metadata,
        )

        # Call LLM with retries
        for attempt in range(self.max_retries):
            try:
                response = self._call_llm(prompt, temperature)
                llm_response = self._parse_response(response, warehouse_id)
                return llm_response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise LLMError(f"Failed to generate config after {self.max_retries} attempts: {str(e)}")
                # Retry with slightly higher temperature
                temperature = min(1.0, temperature + 0.1)

        raise LLMError("Unexpected error in config generation")

    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call the Databricks serving endpoint.

        Args:
            prompt: Prompt to send to LLM
            temperature: Sampling temperature

        Returns:
            LLM response text

        Raises:
            LLMError: If API call fails
        """
        try:
            # Get the serving endpoint
            endpoint = self.client.serving_endpoints.get(name=self.serving_endpoint_name)

            # Build request
            request_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": temperature,
                "max_tokens": 4000,
            }

            # Make request using httpx (Databricks SDK doesn't have direct serving endpoint query)
            host = self.client.config.host
            token = self.client.config.token

            if not token:
                raise LLMError("No authentication token available for serving endpoint")

            url = f"{host}/serving-endpoints/{self.serving_endpoint_name}/invocations"

            with httpx.Client() as http_client:
                response = http_client.post(
                    url,
                    json=request_data,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=120.0,
                )
                response.raise_for_status()

            result = response.json()

            # Extract response text
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise LLMError(f"Unexpected response format: {result}")

        except httpx.HTTPError as e:
            raise LLMError(f"HTTP error calling serving endpoint: {str(e)}")
        except Exception as e:
            raise LLMError(f"Error calling LLM: {str(e)}")

    def _parse_response(self, response: str, warehouse_id: str) -> LLMResponse:
        """Parse LLM response into structured format.

        Args:
            response: Raw LLM response text
            warehouse_id: Warehouse ID to inject if missing

        Returns:
            Parsed LLMResponse

        Raises:
            LLMError: If parsing fails
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON directly
                json_str = response

            # Parse JSON
            data = json.loads(json_str)

            # Inject warehouse_id if missing
            if "genie_space_config" in data:
                if not data["genie_space_config"].get("warehouse_id"):
                    data["genie_space_config"]["warehouse_id"] = warehouse_id

            # Validate with Pydantic
            llm_response = LLMResponse(**data)
            return llm_response

        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse JSON response: {str(e)}\nResponse: {response[:500]}")
        except Exception as e:
            raise LLMError(f"Failed to parse LLM response: {str(e)}")
