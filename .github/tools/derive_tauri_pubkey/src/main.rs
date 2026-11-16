use base64::{engine::general_purpose::STANDARD, Engine as _};
use minisign::{PublicKey, SecretKey, SecretKeyBox, SignatureBox};
use std::{env, error::Error, fs, path::Path};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    if args.get(1).map(|x| x.as_str()) == Some("verify") {
        if args.len() != 5 { return Err("usage: verify <derived-public-b64-path> <exe-path> <sig-path>".into()); }
        let pubkey_encoded=fs::read_to_string(&args[2])?;
        let public_text=String::from_utf8(STANDARD.decode(pubkey_encoded.trim())?)?;
        let keyline=public_text.lines().find(|line| line.starts_with("RW")).ok_or("Invalid Minisign public key")?;
        let public=PublicKey::from_base64(keyline)?;
        let signature_text=fs::read_to_string(&args[4])?;
        // Tauri's updater .sig has had both native Minisign text and an
        // additional base64 wrapper across packaging versions.
        let signature=if let Ok(parsed)=SignatureBox::from_string(&signature_text) {
            parsed
        } else {
            let decoded=STANDARD.decode(signature_text.trim())?;
            SignatureBox::from_string(&String::from_utf8(decoded)?)?
        };
        minisign::verify(&public,&signature,fs::File::open(&args[3])?,true,false,false)?;
        println!("CRYPTOGRAPHIC_INSTALLER_SIGNATURE_VERIFIED=true");
        return Ok(());
    }
    // This tool only runs on the GitHub runner. Never write or print a private key.
    let output = args.get(1).ok_or("expected output path argument")?;
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
    let mut private = None;
    for candidate in &candidates {
        let mut choices = vec![candidate.trim().to_owned()];
        for line in candidate.lines() {
            if !line.starts_with("untrusted comment:") && !line.trim().is_empty() {
                choices.push(format!("untrusted comment: minisign secret key\n{}\n", line.trim()));
            }
        }
        for choice in choices {
            if let Ok(secret_box) = SecretKeyBox::from_string(&choice) {
                if let Ok(secret) = SecretKey::from_box(secret_box, Some(pass.clone())) {
                    private = Some(secret);
                    break;
                }
            }
        }
        if private.is_some() { break; }
    }
    let private = private.ok_or("could not load existing Tauri signing private key; invalid key or passphrase")?;
    let public = PublicKey::from_secret_key(&private)?;
    let output_key = STANDARD.encode(public.to_box()?.into_string().as_bytes());
    // The public key can be shared. Keep its value out of logs to avoid accidental
    // confusion with sensitive keys; the installer will embed it.
    fs::write(&output, output_key)?;
    println!("PUBLIC_DERIVATION=success");
    Ok(())
}
