###
# Copyright (2025) Hewlett Packard Enterprise Development LP
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
# ###
import time
import threading
from rich.progress import Progress, SpinnerColumn, TextColumn

class ProgressBar:
    def __init__(self):
        # Event used for signaling when the task is done
        self.task_done = threading.Event()  

    def show_progress_bar(self, desc):
        # Display the progress bar with a spinner and description
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # Add a task with the given description
            task_id = progress.add_task(desc, total=None)
            # Loop until the task_done event is set
            while not self.task_done.is_set():  
                time.sleep(0.1)
            # Mark the task as completed
            progress.update(task_id, completed=1)  

    def start_progress_bar(self, desc="Processing..."):
        # Start the progress bar in a separate thread
        self.progress_thread = threading.Thread(target=self.show_progress_bar, args=(desc,))
        self.progress_thread.start()

    def stop_progress_bar(self):
        # Signal the thread to stop and wait for it to finish
        self.task_done.set()
        self.progress_thread.join()