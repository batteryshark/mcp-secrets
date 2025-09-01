use eframe::egui;
use serde::Deserialize;
use std::collections::HashMap;
use std::env;
use std::io::{self, Read};
use std::process;

// No changes needed to the data structures. They are well-defined.
#[derive(Deserialize, Debug, Clone)]
struct DialogTemplate {
    title: String,
    description: Option<String>,
    fields: Vec<DialogField>,
}

#[derive(Deserialize, Debug, Clone)]
struct DialogField {
    name: String,
    label: String,
    field_type: Option<String>,
    required: Option<bool>,
    default: Option<String>,
    placeholder: Option<String>,
    help_text: Option<String>,
}

impl DialogField {
    fn is_required(&self) -> bool {
        self.required.unwrap_or(false)
    }

    fn is_password(&self) -> bool {
        self.field_type.as_deref() == Some("password")
    }

    fn get_default(&self) -> String {
        self.default.clone().unwrap_or_default()
    }
}

impl DialogTemplate {
    fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }
}

fn serialize_result(fields: &HashMap<String, String>) -> Result<String, serde_json::Error> {
    serde_json::to_string(fields)
}

struct DialogApp {
    template: DialogTemplate,
    field_values: HashMap<String, String>,
    completed: bool,
    cancelled: bool,
    error_message: Option<String>,
}

impl DialogApp {
    fn new(template: DialogTemplate) -> Self {
        let mut field_values = HashMap::new();
        
        // Initialize with default values. This part is correct.
        for field in &template.fields {
            field_values.insert(field.name.clone(), field.get_default());
        }
        
        Self {
            template,
            field_values,
            completed: false,
            cancelled: false,
            error_message: None,
        }
    }

    /// Validates the form fields and updates the error message if needed.
    /// Returns true if validation passes.
    fn validate_and_submit(&mut self) -> bool {
        let mut validation_errors = Vec::new();
        
        for field in &self.template.fields {
            if field.is_required() {
                let value = self.field_values.get(&field.name).map_or("", |v| v.trim());
                if value.is_empty() {
                    validation_errors.push(format!("'{}' is required", field.label));
                }
            }
        }
        
        if validation_errors.is_empty() {
            self.completed = true;
            true
        } else {
            self.error_message = Some(validation_errors.join(", "));
            false
        }
    }
}

impl eframe::App for DialogApp {
    /// This is the core UI rendering loop.
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // --- Buttons Panel (Bottom) ---
        // Use a TopBottomPanel to dock the buttons to the bottom of the window.
        // This ensures they are always visible and correctly placed, solving the
        // "extra space underneath" problem.
        egui::TopBottomPanel::bottom("buttons_panel").show(ctx, |ui| {
            ui.add_space(5.0); // Some padding above the buttons
            // Use a right-to-left layout to easily right-align the buttons.
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                // Add OK button first because of the right-to-left layout.
                if ui.add_sized([80.0, 30.0], egui::Button::new("OK")).clicked() {
                    if self.validate_and_submit() {
                        ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                    }
                }
                
                ui.add_space(10.0);
                
                // Add Cancel button.
                if ui.add_sized([80.0, 30.0], egui::Button::new("Cancel")).clicked() {
                    self.cancelled = true;
                    ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                }
            });
            ui.add_space(5.0); // Some padding below the buttons
        });

        // --- Main Content Panel (Central) ---
        // The CentralPanel will fill all remaining space between the top and bottom panels.
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.add_space(10.0);
            
            // Title
            ui.heading(&self.template.title);
            ui.add_space(5.0);

            // Description
            if let Some(desc) = &self.template.description {
                ui.label(egui::RichText::new(desc).color(egui::Color32::GRAY));
                ui.add_space(10.0);
            }
            
            ui.separator();

            // Error message
            if let Some(error) = &self.error_message {
                ui.add_space(5.0);
                ui.colored_label(egui::Color32::RED, error);
                ui.add_space(5.0);
            }
            
            // --- Scrollable Form Fields ---
            // A ScrollArea ensures the form is usable even if it has too many
            // fields to fit in the window.
            egui::ScrollArea::vertical().auto_shrink([false, false]).show(ui, |ui| {
                // Use a Grid layout for the form fields. This is the idiomatic way
                // to create aligned labels and input widgets, solving the problem
                // of wasted horizontal space.
                egui::Grid::new("fields_grid")
                    .num_columns(2)
                    .spacing([10.0, 8.0])
                    .min_col_width(100.0) // Minimum width for labels
                    .show(ui, |ui| {
                        for field in &self.template.fields {
                            // Label with required indicator
                            let mut label_text = field.label.clone();
                            if field.is_required() {
                                label_text.push_str(" *");
                            }
                            ui.label(label_text);
                            
                            // Get a mutable reference to the field's value.
                            let value = self.field_values.get_mut(&field.name).unwrap();
                            
                            // Create the TextEdit widget.
                            let mut text_edit = egui::TextEdit::singleline(value)
                                .hint_text(field.placeholder.as_deref().unwrap_or(""));
                            
                            if field.is_password() {
                                text_edit = text_edit.password(true);
                            }
                            
                            // Add the widget to the UI and get its response.
                            // We use `fill_width` to make the input box expand.
                            let response = ui.add(text_edit.desired_width(f32::INFINITY));

                            // Use hover text for help text. It's cleaner than adding more
                            // text directly to the layout.
                            if let Some(help) = &field.help_text {
                                response.on_hover_text(help);
                            }
                            
                            ui.end_row();
                        }
                    });
            });
        });
    }

    /// This function is called when the application is about to close.
    fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>) {
        if self.completed {
            match serialize_result(&self.field_values) {
                Ok(json) => {
                    println!("{}", json);
                    process::exit(0);
                }
                Err(e) => {
                    eprintln!("Failed to serialize results: {}", e);
                    process::exit(2);
                }
            }
        } else {
            // User cancelled or closed the window.
            process::exit(1);
        }
    }
}

fn main() -> Result<(), eframe::Error> {
    // Reading the JSON template from stdin remains the same.
    let mut template_json = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut template_json) {
        eprintln!("Failed to read from stdin: {}", e);
        process::exit(2);
    }

    if template_json.trim().is_empty() {
        let app_name = env::args().next().unwrap_or_else(|| "dialog_gui".to_string());
        eprintln!("Usage: echo '<json_template>' | {}", app_name);
        eprintln!("         {} < template.json", app_name);
        process::exit(2);
    }

    let template = match DialogTemplate::from_json(&template_json) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("Invalid JSON template: {}", e);
            process::exit(2);
        }
    };

    // --- Window Options ---
    // Instead of calculating height, we now define a reasonable default and minimum size.
    // The layout panels and scroll area will handle the content. This makes the
    // window behavior predictable and robust.
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([450.0, 320.0])      // A good starting size.
            .with_min_inner_size([400.0, 250.0])  // A sensible minimum size.
            .with_resizable(true),
        ..Default::default()
    };

    let title = template.title.clone();
    eframe::run_native(
        &title,
        options,
        Box::new(|_cc| Ok(Box::new(DialogApp::new(template)))),
    )
}
