#include <gpiod.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    const char *chip_path = "/dev/gpiochip0";
    const unsigned int gpio_offset = 17;  // BCM GPIO17, physical pin 11 on Raspberry Pi

    // Open the GPIO chip — the kernel device that exposes a bank of GPIO lines.
    // On Raspberry Pi, gpiochip0 covers all the header pins.
    struct gpiod_chip *chip = gpiod_chip_open(chip_path);
    if (!chip) {
        perror("gpiod_chip_open");
        return EXIT_FAILURE;
    }

    // Allocate a settings object describing the electrical/logical behaviour
    // of a line: direction, drive mode, bias, edge detection, etc.
    struct gpiod_line_settings *settings = gpiod_line_settings_new();
    if (!settings) {
        perror("gpiod_line_settings_new");
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    // Configure the line as a push-pull digital output.
    gpiod_line_settings_set_direction(
        settings,
        GPIOD_LINE_DIRECTION_OUTPUT
    );

    // Set the initial output value to ACTIVE (logic high) so the LED turns on
    // as soon as the line is requested, before any explicit set_value call.
    gpiod_line_settings_set_output_value(
        settings,
        GPIOD_LINE_VALUE_ACTIVE
    );

    // Allocate a line config — a mapping that associates one or more line
    // offsets with their settings. Multiple lines can share the same settings
    // object, or each can have different settings within one config.
    struct gpiod_line_config *line_config = gpiod_line_config_new();
    if (!line_config) {
        perror("gpiod_line_config_new");
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    // Bind the settings to offset 17. The third argument is the number of
    // offsets in the array, allowing bulk assignment (e.g. 3 LEDs at once).
    if (gpiod_line_config_add_line_settings(
            line_config,
            &gpio_offset,
            1,
            settings
        ) < 0) {
        perror("gpiod_line_config_add_line_settings");
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    // Allocate a request config — metadata about the requester itself,
    // separate from what lines are being requested or how they are configured.
    struct gpiod_request_config *request_config = gpiod_request_config_new();
    if (!request_config) {
        perror("gpiod_request_config_new");
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    // Set a consumer label visible in /sys/kernel/debug/gpio and to other
    // processes, useful for debugging ownership of lines.
    gpiod_request_config_set_consumer(request_config, "led-c-example");

    // Atomically claim all lines described by line_config from the chip.
    // On success the lines are driven immediately (GPIO17 goes high here).
    // Returns a handle used for all subsequent value reads/writes.
    struct gpiod_line_request *request =
        gpiod_chip_request_lines(chip, request_config, line_config);

    if (!request) {
        perror("gpiod_chip_request_lines");
        gpiod_request_config_free(request_config);
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    // LED is already ON from the initial output value set above.
    printf("GPIO%u LED is ON for 5 seconds, then blinking 10 times\n", gpio_offset);
    sleep(5);

    for (int i = 0; i < 10; i++) {
        // Drive the line high — LED on.
        printf("Blink %d: GPIO%u LED ON\n", i + 1, gpio_offset);
        gpiod_line_request_set_value(request, gpio_offset, GPIOD_LINE_VALUE_ACTIVE);
        usleep(500000);  // 500 ms

        // Drive the line low — LED off.
        printf("Blink %d: GPIO%u LED OFF\n", i + 1, gpio_offset);
        gpiod_line_request_set_value(request, gpio_offset, GPIOD_LINE_VALUE_INACTIVE);
        usleep(500000);  // 500 ms
    }

    printf("GPIO%u LED blink sequence complete\n", gpio_offset);

    // Release resources in reverse acquisition order.
    // Releasing the request drops kernel ownership of the GPIO line;
    // the kernel will also do this automatically if the process exits.
    gpiod_line_request_release(request);
    gpiod_request_config_free(request_config);
    gpiod_line_config_free(line_config);
    gpiod_line_settings_free(settings);
    gpiod_chip_close(chip);

    return EXIT_SUCCESS;
}
