sdk_output=$output_dir/sdk/$sdk_distro/sdk_$sdk_version/isp-sdk-skel
sdk_dir=$output_dir/sdk/$sdk_distro/sdk_$sdk_version

copy_distro_specific() {
    rm -rf $sdk_dir
    mkdir -p $sdk_dir
    pushd $sdk_dir
    rpmwand init isp-sdk
    rm -rf isp-sdk-skel/*
    popd
    cp $distro_specific/isp-sdk.spec.in $sdk_dir/
}

build_package() {
    pushd $sdk_dir
    rpmwand files isp-sdk
    # hack to deal with the fact that `rpmwand files` includes things it should
    # not
    sed -i '/^%dir \/usr\/bin$/d' isp-sdk-files.txt
    rpmwand build isp-sdk $sdk_version 0 x86_64
    popd
    cp $sdk_dir/RPMS/x86_64/isp-sdk-$sdk_version-0.x86_64.rpm $package_dir
}
