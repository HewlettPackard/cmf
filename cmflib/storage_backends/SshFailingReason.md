Why close() exists for SSH but not minio/local/S3:
SSH is the only backend that maintains a persistent connection object (_ssh + _sftp) that lives across multiple calls inside sshremote_artifacts.py. Minio, local, and S3 create/close their connections internally per call. So SSH is the only one that needs an explicit close() from the caller.



Good catch — comparing the original vs current code reveals **4 real bugs** that were fixed:

---

**Bug 1: `sftp.put()` used instead of `sftp.get()`** (both methods)

`put()` = **upload** (local → remote). `get()` = **download** (remote → local).
The original code was trying to *upload* when it should be *downloading*. That's the root cause of pull failing.

```python
# ORIGINAL (wrong) — uploads local file to remote
sftp.put(object_name, abs_download_loc)

# FIXED — downloads remote file to local
sftp.get(object_name, abs_download_loc)
```

---

**Bug 2: `sftp.close()` called inside the loop** (`download_directory`)

```python
# ORIGINAL — closes connection after 1st file, 2nd file onwards fails
for file_info in tracked_files:
    sftp.put(...)
    sftp.close()   # ← kills connection mid-loop!
    ssh.close()
```
Fixed by moving `close()` outside the loop entirely.

---

**Bug 3: Wrong integrity check** (`download_file`)

```python
# ORIGINAL — checks size of a REMOTE path on LOCAL disk = wrong/crashes
local_file_size = os.stat(object_name).st_size

# FIXED — checks remote size before download, local size after
remote_file_size = sftp.stat(object_name).st_size   # remote
local_file_size  = os.stat(abs_download_loc).st_size # local (after download)
```

---

**Bug 4: Wrong variable in inner loop** (`download_directory`)

```python
# ORIGINAL — always downloads the .dir manifest over itself instead of each file
sftp.put(object_name, temp_download_loc)   # object_name = the .dir file

# FIXED — downloads the correct individual file
sftp.get(temp_object_name, temp_download_loc)  # temp_object_name = each file's path
```

---

So the current code is a proper rewrite fixing all 4 bugs, not just comments.