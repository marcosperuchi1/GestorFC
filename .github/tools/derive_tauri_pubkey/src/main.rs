use base64::{engine::general_purpose::STANDARD, Engine as _};
use minisign::{PublicKey, SecretKey, SecretKeyBox};
use std::{env, error::Error, fs, path::Path};

fn main() -> Result<(), Box<dyn Error>> {
    // This tool only runs on the GitHub runner. Never write or print a private key.
    let output = env::args().nth(1).ok_or("expected output path argument")?;
    let input = env::var("TAURI_SIGNING_PRIVATE_KEY")?;
    let pass = env::var("TAURI_SIGNING_PRIVATE_KEY_PASSWORD").unwrap_or_default();
    let raw = if Path::new(&input).is_file() {
        fs::read_to_string(&input)?
    } else {
        input
    };
    // Tauri keys may be stored as a base64-encoded private .key file or as
    // a direct Minisign key. Try the wrapper, then the unwrapped form.
    let mut candidates = vec![raw.clone()];
    if let Ok(decoded) = STANDARD.decode(raw.trim()) {
        if let Ok(decoded_string) = String::from_utf8(decoded) {
            candidates.insert(0, decoded_string);
        }
    }
    let mut keybox = None;
    for candidate in &candidates {
        for line in candidate.lines() {
            if line.starts_with("untrusted comment:") || line.trim().is_empty() {
                continue;
            }
            if let Ok(parsed) = SecretKeyBox::from_string(line.trim()) {
                keybox = Some(parsed);
                break;
            }
        }
        if keybox.is_some() { break; }
    }
    let private = SecretKey::from_box(keybox.ok_or("could not parse the existing Tauri signing key")?, Some(pass))?;
    let public = PublicKey::from_secret_key(&private)?;
    let output_key = STANDARD.encode(public.to_box()?.into_string().as_bytes());
    // The public key can be shared. Keep its value out of logs to avoid accidental
    // confusion with sensitive keys; the installer will embed it.
    fs::write(&output, output_key)?;
    println!("PUBLIC_DERIVATION=success");
    Ok(())
}
