FROM obolibrary/odkfull

# install some more packages from apt
RUN apt-get install -y aha

# install Rust
WORKDIR /tools
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rust.sh
RUN sh rust.sh -y
ENV PATH="/root/.cargo/bin:$PATH"

# install wiring.py using wiring.rs bindings
WORKDIR /tools
RUN git clone https://github.com/ontodev/wiring.py.git
WORKDIR /tools/wiring.py
RUN git clone https://github.com/ontodev/wiring.rs.git
RUN mv python_module.rs wiring.rs/src/
WORKDIR /tools/wiring.py/wiring.rs
RUN echo 'mod python_module;' >> src/lib.rs
RUN echo '[lib]' >> Cargo.toml
RUN echo 'name="wiring_rs"' >> Cargo.toml
RUN echo 'crate-type = ["cdylib", "lib"]' >> Cargo.toml
RUN echo '' >> Cargo.toml
RUN echo '[[bin]]' >> Cargo.toml
RUN echo 'name = "mybin"' >> Cargo.toml
RUN echo 'path = "src/main.rs"' >> Cargo.toml
RUN echo '' >> Cargo.toml
RUN echo '[dependencies.pyo3]' >> Cargo.toml
RUN echo 'version = "0.14.5"' >> Cargo.toml
RUN echo 'features = ["extension-module", "abi3-py36"]' >> Cargo.toml

RUN pip install -U pip maturin
RUN maturin build
RUN pip install target/wheels/wiring_rs-0.1.0-cp36-abi3-manylinux_2_28_x86_64.whl

# install nanobot
WORKDIR /tools
RUN git clone https://github.com/ontodev/nanobot.git
WORKDIR /tools/nanobot
RUN pip install -e .

# install OBI Python requirements
WORKDIR /tools
COPY requirements.txt /tools/obi-requirements.txt
RUN pip install -r obi-requirements.txt

# restore WORKDIR
WORKDIR /tools
