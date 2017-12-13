@setup "Cleanup Before Test" {
       rm -rf /isp-project
}

@teardown "Cleanup After Test" {
       rm -rf /isp-project
}

@test "Test Getting Started Documentation" {
      # Create the project
      isp-create-project /isp-project

      # Build the configuration and policy
      cd /isp-project
      source activate
      make configure
      POLICY_FILES=RWXPolicy make policy

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
