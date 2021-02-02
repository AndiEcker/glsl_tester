""" android constants and helper functions """
import os
from ae.base import os_platform

if os_platform == 'android':
    # noinspection PyUnresolvedReferences
    from android.permissions import request_permissions, Permission  # type: ignore
    from jnius import autoclass


    def log(log_level: str, message: str, file_path: str = ""):
        """ print log message. """
        if not file_path:
            file_path = f"ae_droid_{log_level}.log"
        with open(file_path, 'a') as fp:
            fp.write(message + "\n")


    PACKAGE_NAME = 'package'
    PACKAGE_DOMAIN = 'org.test'
    PERMISSIONS = "INTERNET, VIBRATE, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE"

    BUILD_CONFIG_FILE = 'buildozer.spec'
    if os.path.exists(BUILD_CONFIG_FILE):
        from configparser import ConfigParser

        config = ConfigParser(allow_no_value=True)
        config.optionxform = lambda value: value
        config.read(BUILD_CONFIG_FILE, "utf-8")
        PACKAGE_NAME = config.get('app', 'package.name', fallback=PACKAGE_NAME)
        PACKAGE_DOMAIN = config.get('app', 'package.domain', fallback=PACKAGE_DOMAIN)
        PERMISSIONS = config.get('app', 'android.permissions', fallback=PERMISSIONS)
    else:
        log('debug', f"{BUILD_CONFIG_FILE} is not bundled into the APK - using defaults")

    # request app/service permissions
    permissions = list()
    for permission_str in PERMISSIONS.split(','):
        permission = getattr(Permission, permission_str.strip(), None)
        if permission:
            permissions.append(permission)
    request_permissions(permissions)


    def start_service(service_arg: str = ""):
        """ start service.

        :param service_arg:     string value to be assigned to environment variable PYTHON_SERVICE_ARGUMENT on start.

        see https://github.com/tshirtman/kivy_service_osc/blob/master/src/main.py
        and https://python-for-android.readthedocs.io/en/latest/services/#arbitrary-scripts-services
        """
        service_instance = autoclass(f"{PACKAGE_DOMAIN}.{PACKAGE_NAME}.Service{PACKAGE_NAME.capitalize()}")
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        service_instance.start(activity, service_arg)        # service_arg will be in env var PYTHON_SERVICE_ARGUMENT

        return service_instance
