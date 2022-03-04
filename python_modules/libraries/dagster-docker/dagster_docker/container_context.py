from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional

from dagster import check
from dagster.config.validate import process_config
from dagster.core.errors import DagsterInvalidConfigError
from dagster.core.storage.pipeline_run import PipelineRun

from .utils import DOCKER_CONTAINER_CONTEXT_SCHEMA

if TYPE_CHECKING:
    from . import DockerRunLauncher


class DockerContainerContext(
    NamedTuple(
        "_DockerContainerContext",
        [
            ("registry", Optional[Dict[str, str]]),
            ("env_vars", List[str]),
            ("networks", List[str]),
            ("container_kwargs", Optional[Dict[str, Any]]),
        ],
    )
):
    def __new__(
        cls,
        registry: Optional[Dict[str, str]] = None,
        env_vars: Optional[List[str]] = None,
        networks: Optional[List[str]] = None,
        container_kwargs: Optional[Dict[str, Any]] = None,
    ):
        return super(DockerContainerContext, cls).__new__(
            cls,
            registry=check.dict_param(registry, "registry") if registry != None else None,
            env_vars=check.opt_list_param(env_vars, "env_vars", of_type=str),
            networks=check.opt_list_param(networks, "networks", of_type=str),
            container_kwargs=(
                check.dict_param(container_kwargs, "container_kwargs")
                if container_kwargs != None
                else None
            ),
        )

    def merge(self, other: "DockerContainerContext"):
        return DockerContainerContext(
            registry=other.registry if other.registry != None else self.registry,
            env_vars=self.env_vars + other.env_vars,
            networks=self.networks + other.networks,
            container_kwargs=other.container_kwargs
            if other.container_kwargs != None
            else self.container_kwargs,
        )

    @staticmethod
    def create_for_run(pipeline_run: PipelineRun, run_launcher: Optional["DockerRunLauncher"]):

        context = DockerContainerContext()

        # First apply the instance / run_launcher-level context
        if run_launcher:
            context = context.merge(
                DockerContainerContext(
                    registry=run_launcher.registry,
                    env_vars=run_launcher.env_vars,
                    networks=run_launcher.networks,
                    container_kwargs=run_launcher.container_kwargs,
                )
            )

        run_container_context = (
            pipeline_run.pipeline_code_origin.repository_origin.container_context
            if pipeline_run.pipeline_code_origin
            else None
        )

        if not run_container_context:
            return context

        return context.merge(DockerContainerContext.create_from_config(run_container_context))

    @staticmethod
    def create_from_config(run_container_context):
        run_docker_container_context = (
            run_container_context.get("docker", {}) if run_container_context else {}
        )

        if not run_docker_container_context:
            return DockerContainerContext()

        processed_container_context = process_config(
            DOCKER_CONTAINER_CONTEXT_SCHEMA, run_docker_container_context
        )

        if not processed_container_context.success:
            raise DagsterInvalidConfigError(
                "Errors while parsing Docker container context",
                processed_container_context.errors,
                run_docker_container_context,
            )

        processed_context_value = processed_container_context.value

        return DockerContainerContext(
            registry=processed_context_value.get("registry"),
            env_vars=processed_context_value.get("env_vars", []),
            networks=processed_context_value.get("networks", []),
            container_kwargs=processed_context_value.get("container_kwargs"),
        )
