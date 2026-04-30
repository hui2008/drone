# Rover global object and extern

In `Rover/Rover.h`, this line:

```cpp
extern Rover rover;
```

is a declaration, not a definition. It tells any source file that includes `Rover.h` that a global object named `rover` exists somewhere else.

The actual object is defined once in `Rover/Rover.cpp`:

```cpp
Rover rover;
AP_Vehicle& vehicle = rover;
```

`extern` means: the variable is defined in another translation unit, but this file is allowed to refer to it.

This declaration is placed in the header so Rover source files can access the shared global vehicle object simply by including `Rover.h`. For example, `Rover/mode.cpp` uses it as `rover.ahrs`, `rover.g`, `rover.g2`, and other members.

If `Rover.h` contained `Rover rover;` instead, every `.cpp` file including the header would create its own definition, causing duplicate symbol linker errors and violating C++'s one-definition rule.

The pattern is therefore:

```cpp
// Rover.h
extern Rover rover;   // declaration

// Rover.cpp
Rover rover;          // single definition
```
