# How to Use TensorBoard with CMF
1. Go to the folder where you created your pipeline. In this example, the folder name is "example-get-started".

2. Install the TensorFlow library in the current directory using the following command:
     ```bash
     pip install tensorflow
     ```
     
3. Go to the [tensorboard documentation](https://www.tensorflow.org/tensorboard/get_started) and copy the necessary code.

4. Create a new Python file (e.g., `tensorflow_log.py`) and paste the copied code into this file. Save the file.

5. Execute the TensorFlow log script using the following command:
     ```bash
     python3 tensorflow_log.py
     ```

6. The above script will automatically create a `/logs` directory inside your current directory.

7. Start the CMF server and configure the CMF client.

8. Run the test script to generate the MLMD file using the following command:
     ```bash
     sh test_script.sh
     ```

9. Push the generated MLMD and TensorFlow log files to the CMF server using the following command:
     ```bash
     cmf metadata push -p "pipeline-name" -t "tensorboard-log-file-name"
     ```

10. Go to the CMF server and navigate to the TensorBoard tab. You will see an interface similar to the following image.
    ![image](https://h-huang.github.io/tutorials/_images/tensorboard_scalars.png)

---
