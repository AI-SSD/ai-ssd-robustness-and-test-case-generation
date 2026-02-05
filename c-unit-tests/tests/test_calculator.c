#include <stdio.h>
#include "calculator.h"
#include <assert.h>

static void test__logic__add(void) {
    assert(add(1, 2) == 3);
    assert(add(-1, -2) == -3);
    assert(add(0, 0) == 0);
}

static void test__boundary__multiply(void) {
    assert(multiply(5, 6) == 30);
    assert(multiply(-5, 6) == -30);
    assert(multiply(5, -6) == -30);
    assert(multiply(-5, -6) == 30);
    assert(multiply(0, 100) == 0);
    assert(multiply(100, 0) == 0);
}

static void test__error__multiply_by_zero(void) {
    assert(multiply(5, 0) == 0); // Ensure zero multiplication
    assert(multiply(0, 5) == 0);
}

int main() {
    test__logic__add();
    printf("✓ PASS: test__logic__add\n");

    test__boundary__multiply();
    printf("✓ PASS: test__boundary__multiply\n");

    test__error__multiply_by_zero();
    printf("✓ PASS: test__error__multiply_by_zero\n");

    return 0;
}