fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .out_dir("src/generated")
        .compile(
            &["../../protos/tool.proto"],
            &["../../protos"],
        )?;

    println!("cargo:rerun-if-changed=../../protos/tool.proto");

    Ok(())
}
