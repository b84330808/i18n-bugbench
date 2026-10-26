# `path` prompt in directory mode can't descend into a directory with `\` on Windows

On Windows, the `path` prompt with `directory: true` doesn't let the user enter a directory with the native separator. Typing `C:\project\` shows "No matches found", and pressing Enter only reports "Please select a path". Typing `C:\project/` works.

The same happens when `initialValue` already ends in a backslash:

```ts
const dir = await path({ message: 'Pick a folder', directory: true, initialValue: 'C:\project\' });
// Enter: "Please select a path", instead of selecting the first child directory
```

Expected: on Windows a trailing `\` works like a trailing `/`: the prompt lists the directory's children, and Enter selects the highlighted child (for `C:\tmp\` containing `foo\` and `hello\`, the result is `C:\tmp\foo`). Behaviour on POSIX systems stays as it is.
