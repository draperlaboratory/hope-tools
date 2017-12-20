sdk_output=$output_dir/sdk/ubuntu16/sdk_$sdk_version

copy_distro_specific() {
    rm -rf $sdk_output
    mkdir -p $sdk_output
    mkdir -p $sdk_output/DEBIAN
    m4 --define=SDKVERSION=$sdk_version \
       $distro_specific/control.m4 > $sdk_output/DEBIAN/control
    cp $distro_specific/postinst $sdk_output/DEBIAN/
}

build_package() {
    if [ "$fast_build" = true ]; then
        dpkg_options=-z0
    fi

    pushd $package_dir
    dpkg-deb $dpkg_options --build $sdk_output .
    popd
}
