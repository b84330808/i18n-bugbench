# Files whose full path is longer than MAX_PATH are silently left out on Windows

On Windows, `lsd` does not list a file once its full path is longer than 260 characters (`MAX_PATH`). No error is printed; the file is simply missing, even with `-a`/`--all`. It only shows up with `--system-protected`, as if it were a hidden system file.

For example, in a temporary directory such as `C:\Users\me\AppData\Local\Temp\xyz`, create a file whose name is 250 `a` characters plus `.txt`. `lsd <dir>` prints nothing, and `lsd --all <dir>` prints only `.` and `..`.

`dir` and Explorer list the file normally, and its attributes are ordinary (not hidden, not system).

Expected: such files are listed like any other file, with and without `--all`.
