# GPIO C Build Notes

## What `pkg-config` is for

`pkg-config` helps build tools find installed native libraries. It can report the
compiler and linker flags needed for a dependency, instead of hardcoding paths.

Example:

```bash
pkg-config --cflags --libs libgpiod
```

For this project, it reports:

```bash
-lgpiod
```

That means the `libgpiod` headers and library are available in standard system
locations, and the program only needs to link with `gpiod`.

## What `-l` means

`-l` is a linker flag. It tells the linker to link against a library.

Example:

```bash
-lgpiod
```

This means the linker should look for a library named:

```text
libgpiod.so
```

or:

```text
libgpiod.a
```

## GCC flags used

These are the GCC options used or discussed while building this example.

## Common Makefile flag variables

These variable names are Makefile conventions. They are not all GCC-only, but
GCC and many build systems understand the same pattern.

### `CPPFLAGS`

`CPPFLAGS` means C preprocessor flags. The `CPP` part means C PreProcessor, not
C++.

Common uses:

```make
CPPFLAGS += -I/usr/include/some-library
CPPFLAGS += -DDEBUG
CPPFLAGS += -DVERSION=\"1.0\"
```

Typical flags:

- `-I...`: add a header search path
- `-DNAME`: define a preprocessor macro
- `-DNAME=value`: define a macro with a value
- `-UNAME`: undefine a macro

### `CFLAGS`

`CFLAGS` is for C compiler flags.

Common uses:

```make
CFLAGS += -Wall -Wextra -Wpedantic
CFLAGS += -std=c11
CFLAGS += -g
CFLAGS += -O2
```

Typical flags:

- `-Wall`: enable common warnings
- `-Wextra`: enable extra warnings
- `-Wpedantic`: warn about non-standard C extensions
- `-std=c11`: compile as C11
- `-g`: include debug symbols
- `-O0`, `-O1`, `-O2`, `-O3`: optimization levels

### `CXXFLAGS`

`CXXFLAGS` is for C++ compiler flags.

Example:

```make
CXXFLAGS += -Wall -Wextra -std=c++17
```

### `LDFLAGS`

`LDFLAGS` is for linker options, especially library search paths or linker
behavior.

Common uses:

```make
LDFLAGS += -L/usr/local/lib
LDFLAGS += -Wl,-rpath,/usr/local/lib
```

Typical flags:

- `-L...`: add a library search path
- `-Wl,...`: pass an option directly to the linker

### `LDLIBS`

`LDLIBS` is for libraries to link against.

Common uses:

```make
LDLIBS += -lgpiod
LDLIBS += -lm
```

Typical flags:

- `-l...`: link against a library

In this project, the Makefile gets `LDLIBS` from `pkg-config`:

```make
LDLIBS += $(shell $(PKG_CONFIG) --libs libgpiod)
```

For `libgpiod`, that expands to:

```text
-lgpiod
```

### `-Wall`

Enables a common set of useful compiler warnings.

This helps catch mistakes such as suspicious expressions, missing return values,
or code that is likely to behave differently than intended.

### `-Wextra`

Enables additional warnings beyond `-Wall`.

This is stricter than `-Wall` and can catch more subtle issues, such as unused
parameters in some cases.

### `-pedantic` / `-Wpedantic`

Warns when the code uses features outside the selected C standard.

The direct GCC command used `-pedantic`. The Makefile uses `-Wpedantic`. For this
project, both are being used as warning-related strictness flags.

### `-o`

Sets the output file name.

Example:

```bash
-o led
```

This tells GCC to name the compiled program `led`. Without `-o`, GCC usually
creates an executable named `a.out`.

### `-l`

Links against a library.

Example:

```bash
-lgpiod
```

This tells the linker to link against `libgpiod.so` or `libgpiod.a`.

### `-I`

Adds a header include search path.

Example:

```bash
-I/usr/include/some-library
```

This tells GCC to also search that directory when resolving `#include` files.

We did not need a custom `-I` path for this build because `pkg-config --cflags
libgpiod` did not report one. The `gpiod.h` header was available from GCC's
default include paths.

You can inspect GCC's default include paths with:

```bash
gcc -E -x c - -v < /dev/null
```

## Compile command

The GPIO example was compiled with:

```bash
gcc -Wall -Wextra -pedantic main.c -o led -lgpiod
```

From the repository root, the equivalent command is:

```bash
gcc -Wall -Wextra -pedantic my/gpio/main.c -o my/gpio/led -lgpiod
```

The output binary is:

```text
my/gpio/led
```
