import os
import traceback
from joblib import Parallel, delayed

from .profile import Profile

from .schedule_utils import ScheduleUtils
from .create_driver import BrowserConfig, create_driver
from .botasaurus_driver import BotasaurusDriver
from .utils import relative_path,merge_dicts_in_one_dict, write_file, write_html, write_json,get_driver_path
from .local_storage import LocalStorage
from .analytics import Analytics
from .task_info import TaskInfo
from .task_config import TaskConfig

class RetryException(Exception):
    pass

def get_driver_url_safe(driver):
    try:
        return driver.current_url
    except:
        return "Failed to get driver url"

def get_page_source_safe(driver):
    try:
        return driver.page_source
    except:
        return "Failed to get page_source"


def _download_driver():
    from .download_driver import download_driver
    download_driver()

class BaseTask():
    def __init__(self):
        self.task_path = None
        self.task_id = None        


    task_config = TaskConfig()

    def get_task_config(self):
        return self.task_config

    browser_config = BrowserConfig()

    def get_browser_config(self, data):
        return self.browser_config


    data = [None]
    def get_data(self):
        return self.data


    def schedule(self, data):
        """
            Seconds delay between each run
        """
        return ScheduleUtils.no_delay(data)



        
    def set_config_on_driver(self, driver):
            driver.task_id = self.task_id
            driver.task_path = self.task_path
            driver.beep = self._task_config.beep

    def create_driver(self, config: BrowserConfig):
        driver =  create_driver(config)
        self.set_config_on_driver(driver)
        return driver
    
    def divide_list(self, input_list, num_of_groups=8, skip_if_less_than=1):
        if skip_if_less_than is not None and len(input_list) < skip_if_less_than:
            return [input_list]

        group_size = len(input_list) // num_of_groups
        remainder = len(input_list) % num_of_groups

        divided_list = []
        for i in range(num_of_groups):
            start_index = i * group_size
            end_index = start_index + group_size
            divided_list.append(input_list[start_index:end_index])

        if remainder:
            for i in range(remainder):
                element = input_list[-i - 1]
                idx = i % num_of_groups
                # print(idx, element)
                divided_list[idx].append(element)

        return divided_list

    def merge_list(self, input_list):
        flattened_list = []
        for item in input_list:
            flattened_list.extend(item)
        return flattened_list

    # simple headless drivers no profile options
    def parallel(self, callable, data_list= [None], n = 2):
        def run(data):
            config = self.get_browser_config(data)
            driver = self.create_driver(config)
            result = []
            try:
                result = callable(driver, data)
            except Exception as e:

              if not self._task_config.close_on_crash:
                traceback.print_exc()
                driver.prompt("We've paused the browser to help you debug. Press 'Enter' to close.")
              else:
                raise e
            driver.close()
            return result
        
        n = min(len(data_list), n)

        result = (Parallel(n_jobs=n, backend="threading")(delayed(run)(l) for l in data_list))
        return result 
        

    def begin_task(self, data, task_config:TaskConfig):
        def create_directories(task_path):

            driver_path =  relative_path(get_driver_path(), 0)
            if not os.path.isfile(driver_path):
                _download_driver()

            tasks_path =  relative_path('tasks/', 0)
            if not os.path.exists(tasks_path):
                os.makedirs(tasks_path)

            output_path =  relative_path('output/', 0)
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            profiles_path =  relative_path('profiles/', 0)
            if not os.path.exists(profiles_path):
                os.makedirs(profiles_path)

            path =  relative_path(task_path, 0)
            if not os.path.exists(path):
                os.makedirs(path)

        
        def run_task(is_retry, retry_attempt):
            # print('Launching Task')
            task = TaskInfo()
            task_name = self.__class__.__name__
            task.set_task_name(task_name)

            final_image = "final.png"
            def end_task(driver:BotasaurusDriver):
                task.end()
                task.set_ip()
                data = task.get_data()
                # driver.save_screenshot(final_image)
                
                html_path  = f'{self.task_path}/page.html'
                source = get_page_source_safe(driver)
                # write_html(source, html_path)

                data["last_url"] = get_driver_url_safe(driver)
                
                if is_retry: 
                    data["is_retry"] = is_retry
                    data["retry_attempt"] = retry_attempt


                task_info_path  = f'{self.task_path}/task_info.json'
                
                if driver._init_data is not None:
                    data = merge_dicts_in_one_dict(data , driver._init_data)
                
                # write_json(data , task_info_path)
                Analytics.send_tracking_data(task_name)
            count = LocalStorage.get_item('count', 0) + 1
            LocalStorage.set_item('count', count)

            self.task_path = f'tasks/{count}' 
            self.task_id = count

            create_directories(self.task_path)
            
            task.start()

            self._task_config = task_config 
            config = self.get_browser_config(data)
            driver = self.create_driver(config)

            if config.profile is not None:
                Profile.profile = config.profile


            self.set_config_on_driver(driver)

            self.beep = task_config.beep

            final_image_path = f'{self.task_path}/{final_image}'
            
            def close_driver(driver:BotasaurusDriver):
                # print("Closing Browser")                
                # set tiny profile data
                driver.close()
                # print("Closed Browser")  

                if self.task_config.log_time:
                    duration = task.get_data()['duration']
                    # print(f'Task done in {duration}.')              

            result = None
            try:
                result = self.run(driver, data)
                end_task(driver)
                close_driver(driver)
                # print(f'View Final Screenshot at {final_image_path}')
                return result
            except RetryException as error:
                end_task(driver)
                close_driver(driver)
                # print('Task is being Retried!')
                return run_task(True, retry_attempt + 1)
            except Exception as error:
                exception_log = traceback.format_exc()
                traceback.print_exc()
                end_task(driver)
                
                error_log_path  = f'{self.task_path}/error.log'
                write_file(exception_log, error_log_path)

                IS_PRODUCTION = os.environ.get("ENV") == "production"

                if not IS_PRODUCTION:
                    if not task_config.close_on_crash:
                        driver.prompt("We've paused the browser to help you debug. Press 'Enter' to close.")
                    
                close_driver(driver)

                # print(f'Task Failed! View Final Screenshot at {final_image_path}')
                return result

        final = run_task(False, 0)

        Profile.profile = None

        return final

    def run(self, driver: BotasaurusDriver, data: any):
        pass

    def is_new_user(self):
        count = LocalStorage.get_item('count', 0)
        return count  <= 5

