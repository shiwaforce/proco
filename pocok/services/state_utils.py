import os
from .catalog_handler import CatalogHandler
from .config_handler import ConfigHandler
from .console_logger import ColorPrint
from .compose_handler import ComposeHandler
from .file_utils import FileUtils
from .project_utils import ProjectUtils
from .state import StateHolder
from .yaml_utils import YamlUtils


class StateUtils:

    PREPARE_STATES = ["config", "catalog_read", "catalog", "project_repo", "project_file", "compose_handler"]

    @staticmethod
    def prepare(prepareable=None):
        if prepareable not in StateUtils.PREPARE_STATES:
            ColorPrint.print_info(message="Unknown prepare command : " + str(prepareable), lvl=1)
            return

        StateUtils.prepare_config()
        if prepareable is not "config":
            StateUtils.prepare_catalog(prepareable)
        if prepareable not in ["config", "catalog_read", "catalog"]:
            StateUtils.prepare_project_repo()
        if prepareable not in ["config", "catalog_read", "catalog", "project_repo"]:
            StateUtils.prepare_project_file()
        if prepareable is "compose_handler":
            StateHolder.compose_handler = ComposeHandler(StateHolder.poco_file)
        StateHolder.process_extra_args()

    @staticmethod
    def prepare_config():
        if StateHolder.global_config_file is None:
            StateHolder.global_config_file = os.path.join(StateHolder.home_dir, '.pocok')
        StateUtils.prepare_config_handler()
        StateHolder.config_handler.read_configs(StateHolder.global_config_file, True)

    @staticmethod
    def prepare_catalog(elem):
        if StateHolder.catalog_config_file is None:
            StateHolder.catalog_config_file = os.path.join(StateHolder.home_dir, 'config')
        StateUtils.prepare_config_handler()
        if os.path.exists(StateHolder.catalog_config_file):
            StateHolder.config_handler.read_catalogs()
            if elem is not "catalog_read":
                CatalogHandler.load()

    @staticmethod
    def prepare_project_repo():
        """Get project parameters form catalog, if it is exists"""

        if StateHolder.name is None:
            return
        for catalog in StateHolder.catalogs:
            if StateHolder.name in StateHolder.catalogs[catalog]:
                StateHolder.catalog_element = StateHolder.catalogs[catalog].get(StateHolder.name)

        if StateHolder.catalog_element is None:
            return
        StateHolder.repository = ProjectUtils.get_project_repository(StateHolder.catalog_element, ssh=None)
        # TODO handle ssh parameter

    @staticmethod
    def prepare_project_file():
        if StateHolder.repository is None:
            StateHolder.poco_file = FileUtils.get_backward_compatible_pocok_file(directory=os.getcwd())
        else:
            StateHolder.poco_file = ProjectUtils.get_compose_file(StateHolder.catalog_element, None, True)

    @staticmethod
    def prepare_config_handler():
        if StateHolder.config_handler is None:
            ConfigHandler()

    @staticmethod
    def calculate_name_and_work_dir():
        arg = StateHolder.args.get('<project/plan>')
        if arg is None:  # if empty
            StateHolder.work_dir = os.getcwd()
            StateHolder.name = FileUtils.get_directory_name()
        elif '/' in arg:  # if have '/'
            project_and_plan = arg.split("/", maxsplit=2)
            StateHolder.name = project_and_plan[0]
            StateHolder.plan = project_and_plan[1]
        else:  # need some another checks
            local_project_file = FileUtils.get_backward_compatible_pocok_file()
            if local_project_file is None:
                StateHolder.work_dir = StateHolder.base_work_dir  # check if not default
                StateHolder.name = arg
            else:
                if YamlUtils.check_file(local_project_file, arg):
                    StateHolder.work_dir = os.getcwd()
                    StateHolder.name = FileUtils.get_directory_name()
                    StateHolder.plan = arg
                else:
                    StateHolder.name = arg


    @staticmethod
    def read_project_config_and_catalog():  # TODO
        CatalogHandler.load()
        if StateHolder.name is not None:
            catalog = CatalogHandler.get()
            if catalog is not None:
                StateHolder.config_handler.read_configs(
                    os.path.join(StateHolder.work_dir, catalog.get('repository_dir', StateHolder.name), '.pocok'))
        else:
            """ Read local config """
            StateHolder.config_handler.read_configs(os.path.join(os.getcwd(), '.pocok'))


