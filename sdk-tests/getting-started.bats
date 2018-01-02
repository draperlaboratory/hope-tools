setup() {
    rm -rf /isp-project
}

teardown() {
    rm -rf /isp-project
}

@test "Test Getting Started Documentation" {
    # Create the project
    mkdir /isp-project
    cd /isp-project
    isp-create-pex-dir pex
    source pex/activate
    isp-copy-samples

    # Build the configuration and policy
    isp-build-pex RWXPolicy

    # Run Dover OS hello world sample
    cd samples/hello_world
    POLICIES=rwx make
    rundk --policies=rwx hello_world > rundk.out 2>&1
    grep -q "hello world!" rundk.out

    # Run FreeRTOS hello world sample
    cd /isp-project/FreeRTOS-RISCV/samples/hello_world
    POLICIES=rwx make

    # Using a timeout is really ugly, ideally the desired output string would
    # be searched for with perhaps an extremely long timeout
    runap --policies=rwx --timeout=20 main.rom > runap.out 2>&1
    grep -q "Hello from an ISP FreeRTOS application" runap.out
    grep -q "Hello again, press Ctrl^C twice to exit the simulator" runap.out
}
