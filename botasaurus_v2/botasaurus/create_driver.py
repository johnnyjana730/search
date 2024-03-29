from selenium.common.exceptions import WebDriverException
from .user_agent import UserAgentInstance, UserAgent
from .window_size import WindowSize, WindowSizeInstance
from .utils import NETWORK_ERRORS, get_current_profile_path, is_windows, read_json, relative_path, retry_if_is_error, silentremove
from selenium.webdriver.chrome.options import Options as GoogleChromeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from undetected_chromedriver import ChromeOptions
from .botasaurus_driver import BotasaurusDriver
from .botasaurus_undetected_driver import BotasaurusUndetectedDriver
import shutil
import os


class RetryException(Exception):
    pass

class BrowserConfig:
    def __init__( self, 
                  headless=False,  
                  proxy=None,  
                  lang=None,  
                  use_undetected_driver=False, 
                  block_images = False, 
                  profile=None, 
                  is_tiny_profile=False,
                  user_agent=None,
                  window_size=WindowSize.window_size_1920_1080, 
                  is_eager=False, 
                  ):
        self.user_agent = user_agent
        self.proxy = proxy
        self.headless = headless
        self.lang = lang
        self.window_size = window_size
        self.block_images = block_images


        if profile is not None:
            self.profile = str(profile)
        else:
            self.profile = None
        self.is_eager = is_eager
        self.use_undetected_driver = use_undetected_driver

        self.is_tiny_profile = is_tiny_profile

        if self.is_tiny_profile and self.profile is None:
            raise Exception('Profile must be given when using tiny profile')


def delete_cache(driver):
    print('Deleting Cache')
    driver.command_executor._commands['SEND_COMMAND'] = (
        'POST', '/session/$sessionId/chromium/send_command'
    )
    driver.execute('SEND_COMMAND', dict(
        cmd='Network.clearBrowserCache', params={}))


def add_useragent(options, user_agent):
    options.add_argument(f'--user-agent={user_agent}')


def create_profile_path(user_id):
    PROFILES_PATH = 'profiles'
    PATH = f'{PROFILES_PATH}/{user_id}'
    path = relative_path(PATH, 0)
    return path


def delete_corrupted_files(user_id):
    is_success = silentremove(
        f'{create_profile_path(user_id)}/SingletonCookie')
    silentremove(f'{create_profile_path(user_id)}/SingletonSocket')
    silentremove(f'{create_profile_path(user_id)}/SingletonLock')

    if is_success:
        print('Fixed Profile by deleting Corrupted Files')
    else:
        print('No Corrupted Profiles Found')


def delete_profile_path(user_id):
    path = create_profile_path(user_id)
    shutil.rmtree(path, ignore_errors=True)


def add_essential_options(options, profile, window_size, user_agent):
    options.add_argument("--start-maximized")
    if window_size != WindowSize.REAL:
        if window_size == None:
            if profile == None:
                window_size = WindowSizeInstance.get_random()
            else:
                window_size = WindowSizeInstance.get_hashed(profile)
        else:
            if window_size == WindowSize.RANDOM:
                window_size = WindowSizeInstance.get_random()
            elif window_size == WindowSize.HASHED:
                window_size = WindowSizeInstance.get_hashed(profile)
            else:
                window_size = window_size

        window_size = WindowSize.window_size_to_string(window_size)
        options.add_argument(f"--window-size={window_size}")

    if profile is not None:
        profile = str(profile)

    if user_agent != UserAgent.REAL:
        if user_agent == None:
            if profile == None:
                user_agent = UserAgentInstance.get_random()
            else:
                user_agent = UserAgentInstance.get_hashed(profile)
        else:
            if user_agent == UserAgent.RANDOM:
                user_agent = UserAgentInstance.get_random()
            elif user_agent == UserAgent.HASHED:
                user_agent = UserAgentInstance.get_hashed(profile)
            else:
                user_agent = user_agent

        add_useragent(options, user_agent)

    has_user = profile is not None

    if has_user:
        path = create_profile_path(profile)
        user_data_path = f"--user-data-dir={path}"
        options.add_argument(user_data_path)

    return {"window_size": window_size, "user_agent": user_agent, "profile": profile}


def get_eager_startegy():

    caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    caps["pageLoadStrategy"] = "none"   # Do not wait for full page load
    return caps


def hide_automation_flags(options):
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-blink-features")

    options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # New Options
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")


def is_docker():
    path = '/proc/self/cgroup'

    return (
        os.path.exists('/.dockerenv') or
        os.path.isfile(path) and any('docker' in line for line in open(path))
        or os.environ.get('KUBERNETES_SERVICE_HOST') is not None
    )


def get_driver_path():
    executable_name = "chromedriver.exe" if is_windows() else "chromedriver"
    dest_path = f"build/{executable_name}"
    return dest_path


def load_cookies(driver: BotasaurusDriver, config):
    current_profile = get_current_profile_path(config)
    current_profile_path = relative_path(current_profile, 0)

    if not os.path.exists(current_profile_path):
        os.makedirs(current_profile_path)

    current_profile_data = get_current_profile_path(config) + 'profile.json'
    current_profile_data_path = relative_path(current_profile_data, 0)

    if not os.path.isfile(current_profile_data_path):
        return

    cookies = read_json(current_profile_data_path)
    # Enables network tracking so we may use Network.setCookie method
    driver.execute_cdp_cmd('Network.enable', {})
    # Iterate through pickle dict and add all the cookies
    for cookie in cookies:
        # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
        if 'expiry' in cookie:
            cookie['expires'] = cookie['expiry']
            del cookie['expiry']
        # Replace domain 'apple.com' with 'microsoft.com' cookies
        cookie['domain'] = cookie['domain'].replace(
            'apple.com', 'microsoft.com')
        # Set the actual cookie
        driver.execute_cdp_cmd('Network.setCookie', cookie)

    driver.execute_cdp_cmd('Network.disable', {})


def create_driver(config: BrowserConfig):
    def run():
        is_undetected = config.use_undetected_driver
        options = ChromeOptions() if is_undetected else GoogleChromeOptions()

        if config.headless:
            options.add_argument('--headless=new')

        selwireOptions = None
        if config.proxy is not None:
                selwireOptions = {'proxy': {'http': config.proxy, 'https': config.proxy}}
        
        if is_docker():
            print("Running in Docker, So adding sandbox arguments")
            options.arguments.extend(
                ["--no-sandbox", "--disable-setuid-sandbox"])

        if config.lang is not None:
            options.add_argument(f'--lang={config.lang}')

        if config.block_images:
            options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheet": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                }
            )

        driver_attributes = add_essential_options(
            options, None if config.is_tiny_profile else config.profile, config.window_size, config.user_agent)

        if driver_attributes["profile"] is not None:
            driver_string = "Creating Driver with profile {}, window_size={}, and user_agent={}".format(
                driver_attributes["profile"], driver_attributes["window_size"], driver_attributes["user_agent"])
        else:
            driver_string = "Creating Driver with window_size={} and user_agent={}".format(
                driver_attributes["window_size"], driver_attributes["user_agent"])

        if config.is_eager:
            desired_capabilities = get_eager_startegy()
        else:
            desired_capabilities = None

        # print(driver_string)

        if is_undetected:
            if selwireOptions is not None:
                raise Exception("Cannot use proxy with Undetected Driver")
            driver = BotasaurusUndetectedDriver(
                desired_capabilities=desired_capabilities,
                options=options
            )
        else:
            # options.add_experimental_option("prefs",  {"profile.managed_default_content_settings.images": 2})
            hide_automation_flags(options)

            # CAPTCHA
            options.arguments.extend(
                ["--disable-web-security", "--disable-site-isolation-trials", "--disable-application-cache"])

            path = relative_path(get_driver_path(), 0)
            if selwireOptions is not None:
                from .botasaurus_driver_selenium_wire import BotasaurusDriverSeleniumWire

                driver = BotasaurusDriverSeleniumWire(
                                    desired_capabilities=desired_capabilities,
                                    seleniumwire_options=selwireOptions,
                                    chrome_options=options,
                                    executable_path=path,
                                )  
            else:
                driver = BotasaurusDriver(

                    desired_capabilities=desired_capabilities,
                    chrome_options=options,
                    executable_path=path,
                )
        if driver_attributes["profile"] is None:
            del driver_attributes["profile"]

        driver._init_data = driver_attributes
        return driver
    driver = retry_if_is_error(
        run, NETWORK_ERRORS + [(WebDriverException, lambda: delete_corrupted_files(config.profile) if config.profile else None)], 5)
    # print("Launched Browser")

    if config.is_tiny_profile:
        load_cookies(driver, config)

    driver.browser_config = config
    return driver
