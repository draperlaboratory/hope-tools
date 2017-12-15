sdk_output=$output_dir/ubuntu16/sdk_$sdk_version

copy_distro_specific() {
    mkdir -p $sdk_output/DEBIAN
    m4 --define=SDKVERSION=$sdk_version \
       $distro_specific/control.m4 > $sdk_output/DEBIAN/control
}

build_package() {
    if [ "$fast_build" = true ]; then
        dpkg_options=-z0
    fi

    dpkg-deb $dpkg_options --build $sdk_output .
}
