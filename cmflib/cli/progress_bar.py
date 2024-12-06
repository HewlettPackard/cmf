###
# Copyright (2024) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import time
from tqdm import tqdm
import threading

class ProgressBar:
    # Method to display an indeterminate progress bar
    def show_progress_bar(self) -> None:
        self.task_done = False
        with tqdm(total=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]') as p:
            while not self.task_done:
                # if progress bar is not reaching 100 then update it otherwise wait after reched 100
                if p.n < 100:
                    p.update(1)
                    time.sleep(0.1)
                else:
                    time.sleep(0.1)
            p.update(100-p.n)

    # Method to start the progress bar in a separate thread
    def start_progress_bar(self) -> None:
        self.progress_thread = threading.Thread(target=self.show_progress_bar)
        self.progress_thread.start()

    # Method to stop the progress bar safely
    def stop_progress_bar(self) -> None:
        if hasattr(self, 'progress_thread') and self.progress_thread.is_alive():
            self.task_done = True
            self.progress_thread.join()