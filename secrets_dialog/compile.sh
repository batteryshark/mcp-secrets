#!/bin/bash

cargo build --release

# run the compiled binary with the test template
#./target/release/dialog_gui < test_template.json