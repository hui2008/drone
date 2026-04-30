#include <gpiod.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    const char *chip_path = "/dev/gpiochip0";
    const unsigned int gpio_offset = 17;  // BCM GPIO17, physical pin 11 on Raspberry Pi

    struct gpiod_chip *chip = gpiod_chip_open(chip_path);
    if (!chip) {
        perror("gpiod_chip_open");
        return EXIT_FAILURE;
    }

    struct gpiod_line_settings *settings = gpiod_line_settings_new();
    if (!settings) {
        perror("gpiod_line_settings_new");
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    gpiod_line_settings_set_direction(
        settings,
        GPIOD_LINE_DIRECTION_OUTPUT
    );

    gpiod_line_settings_set_output_value(
        settings,
        GPIOD_LINE_VALUE_ACTIVE
    );

    struct gpiod_line_config *line_config = gpiod_line_config_new();
    if (!line_config) {
        perror("gpiod_line_config_new");
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

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

    struct gpiod_request_config *request_config = gpiod_request_config_new();
    if (!request_config) {
        perror("gpiod_request_config_new");
        gpiod_line_config_free(line_config);
        gpiod_line_settings_free(settings);
        gpiod_chip_close(chip);
        return EXIT_FAILURE;
    }

    gpiod_request_config_set_consumer(request_config, "led-c-example");

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

    printf("LED on GPIO%u is ON for 5 seconds\n", gpio_offset);
    sleep(5);

    if (gpiod_line_request_set_value(
            request,
            gpio_offset,
            GPIOD_LINE_VALUE_INACTIVE
        ) < 0) {
        perror("gpiod_line_request_set_value");
    } else {
        printf("LED is OFF\n");
    }

    gpiod_line_request_release(request);
    gpiod_request_config_free(request_config);
    gpiod_line_config_free(line_config);
    gpiod_line_settings_free(settings);
    gpiod_chip_close(chip);

    return EXIT_SUCCESS;
}
