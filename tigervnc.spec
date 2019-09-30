%global _hardened_build 1

Name:           tigervnc
Version:        1.9.0
Release:        3
Summary:        A TigerVNC remote display system

License:        GPLv2+
URL:            http://www.tigervnc.com

Source0:        %{name}-%{version}.tar.gz
Source1:        vncserver.service
Source2:        vncserver.sysconfig
Source3:        10-libvnc.conf
Source4:        xvnc.service
Source5:        xvnc.socket

Patch1:         tigervnc-manpages.patch
Patch2:         tigervnc-getmaster.patch
Patch3:         tigervnc-shebang.patch
Patch4:         tigervnc-xstartup.patch
Patch5:         tigervnc-utilize-system-crypto-policies.patch
Patch6:         tigervnc-ignore-buttons-in-mouse-leave-event.patch
Patch7:         tigervnc-passwd-crash-with-malloc-checks.patch

Patch100:       tigervnc-xserver120.patch

BuildRequires:  gcc-c++ systemd cmake automake autoconf gettext gettext-autopoint pixman-devel fltk-devel >= 1.3.3
BuildRequires:  libX11-devel libtool libxkbfile-devel libpciaccess-devel libXinerama-devel libXfont2-devel
BuildRequires:  libXext-devel xorg-x11-server-source libXi-devel libXdmcp-devel libxshmfence-devel
BuildRequires:  xorg-x11-xtrans-devel xorg-x11-util-macros xorg-x11-server-devel libXtst-devel libdrm-devel libXt-devel
BuildRequires:  openssl-devel mesa-libGL-devel freetype-devel desktop-file-utils java-devel jpackage-utils pam-devel gnutls-devel libjpeg-turbo-devel

Requires(post): coreutils
Requires(postun):coreutils

Requires:       hicolor-icon-theme
Requires:       tigervnc-license
Requires:       tigervnc-icons

%description
Virtual Network Computing (VNC) is a remote display system which
allows you to view a computing 'desktop' environment not only on the
machine where it is running, but from anywhere on the Internet and
from a wide variety of machine architectures.  This package contains a
client which will allow you to connect to other desktops running a VNC
server.

%package server
Summary:        A TigerVNC server
Requires:       perl-interpreter
Requires:       tigervnc-server-minimal
Requires:       xorg-x11-xauth
Requires:       xorg-x11-xinit
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires(post): systemd

%description server
The VNC system allows you to access the same desktop from a wide
variety of platforms.  This package includes set of utilities
which make usage of TigerVNC server more user friendly. It also
contains x0vncserver program which can export your active
X session.

%package server-minimal
Summary:        A minimal installation of TigerVNC server
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
Requires(post): systemd

Requires:       mesa-dri-drivers, xkeyboard-config, xorg-x11-xkb-utils
Requires:       tigervnc-license

%description server-minimal
The VNC system allows you to access the same desktop from a wide
variety of platforms. This package contains minimal installation
of TigerVNC server, allowing others to access the desktop on your
machine.

%package server-module
Summary:        TigerVNC module to Xorg
Requires:       xorg-x11-server-Xorg %(xserver-sdk-abi-requires ansic) %(xserver-sdk-abi-requires videodrv)
Requires:       tigervnc-license

%description server-module
This package contains libvnc.so module to X server, allowing others
to access the desktop on your machine.

%package server-applet
Summary:        Java TigerVNC viewer applet for TigerVNC server
Requires:       tigervnc-server, java, jpackage-utils
BuildArch:      noarch

%description server-applet
The Java TigerVNC viewer applet for web browsers. Install this package to allow
clients to use web browser when connect to the TigerVNC server.

%package license
Summary:        License of TigerVNC suite
BuildArch:      noarch

%description license
This package contains license of the TigerVNC suite

%package icons
Summary:        Icons for TigerVNC viewer
BuildArch:      noarch

%description icons
This package contains icons for TigerVNC viewer

%prep
%setup -q

cp -r /usr/share/xorg-x11-server-source/* unix/xserver
pushd unix/xserver
for all in `find . -type f -perm -001`; do
        chmod -x "$all"
done
%patch100 -p1 -b .xserver120-rebased
popd

# Synchronise manpages and --help output (bug #980870).
%patch1 -p1 -b .manpages

# libvnc.so: don't use unexported GetMaster function (bug #744881 again).
%patch2 -p1 -b .getmaster

# Don't use shebang in vncserver script.
%patch3 -p1 -b .shebang

# Clearer xstartup file (bug #923655).
%patch4 -p1 -b .xstartup

# Utilize system-wide crypto policies
%patch5 -p1 -b .utilize-system-crypto-policies

%patch6 -p1 -b .ignore-buttons-in-mouse-leave-event

%patch7 -p1 -b .tigervnc-passwd-crash-with-malloc-checks

%build
export CFLAGS="$RPM_OPT_FLAGS -fpic"
export CXXFLAGS="$CFLAGS"

%{cmake} .
make %{?_smp_mflags}

pushd unix/xserver
autoreconf -fiv
%configure \
        --disable-xorg --disable-xnest --disable-xvfb --disable-dmx --disable-xwin --disable-xephyr --disable-kdrive --disable-xwayland \
        --with-pic --disable-static --with-default-font-path="catalogue:%{_sysconfdir}/X11/fontpath.d,built-ins" \
        --with-fontdir=%{_datadir}/X11/fonts --with-xkb-output=%{_localstatedir}/lib/xkb --enable-install-libxf86config \
        --enable-glx --disable-dri --enable-dri2 --disable-dri3 --disable-unit-tests  --disable-config-hal --disable-config-udev \
        --with-dri-driver-path=%{_libdir}/dri --without-dtrace --disable-devel-docs --disable-selective-werror

make %{?_smp_mflags}
popd

# Build icons
pushd media
make
popd

# Build Java applet
pushd java
%{cmake} .
JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF8" make
popd

%install
%make_install
rm -f %{buildroot}%{_docdir}/%{name}-%{version}/{README.rst,LICENCE.TXT}

pushd unix/xserver/hw/vnc
make install DESTDIR=%{buildroot}
popd

# Install systemd unit file
mkdir -p %{buildroot}%{_unitdir}
install -m644 %{SOURCE1} %{buildroot}%{_unitdir}/vncserver@.service
install -m644 %{SOURCE4} %{buildroot}%{_unitdir}/xvnc@.service
install -m644 %{SOURCE5} %{buildroot}%{_unitdir}/xvnc.socket
rm -rf %{buildroot}%{_initrddir}

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/vncservers

# Install desktop stuff
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/{16x16,24x24,48x48}/apps

pushd media/icons
for s in 16 24 48; do
install -m644 tigervnc_$s.png %{buildroot}%{_datadir}/icons/hicolor/${s}x$s/apps/tigervnc.png
done
popd


# Install Java applet
pushd java
mkdir -p %{buildroot}%{_datadir}/vnc/classes
install -m755 VncViewer.jar %{buildroot}%{_datadir}/vnc/classes
install -m644 com/tigervnc/vncviewer/index.vnc %{buildroot}%{_datadir}/vnc/classes
popd

%find_lang %{name} %{name}.lang

# remove unwanted files
rm -f  %{buildroot}%{_libdir}/xorg/modules/extensions/libvnc.la

mkdir -p %{buildroot}%{_sysconfdir}/X11/xorg.conf.d/
install -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/X11/xorg.conf.d/10-libvnc.conf

%post server
%systemd_post vncserver.service
%systemd_post xvnc.service
%systemd_post xvnc.socket

%preun server
%systemd_preun vncserver.service
%systemd_preun xvnc.service
%systemd_preun xvnc.socket

%postun server
%systemd_postun

%files -f %{name}.lang
%doc README.rst
%{_bindir}/vncviewer
%{_datadir}/applications/*
%{_mandir}/man1/vncviewer.1*

%files server
%config(noreplace) %{_sysconfdir}/sysconfig/vncservers
%{_unitdir}/vncserver@.service
%{_unitdir}/xvnc@.service
%{_unitdir}/xvnc.socket
%{_bindir}/x0vncserver
%{_bindir}/vncserver
%{_mandir}/man1/vncserver.1*
%{_mandir}/man1/x0vncserver.1*

%files server-minimal
%{_bindir}/vncconfig
%{_bindir}/vncpasswd
%{_bindir}/Xvnc
%{_mandir}/man1/Xvnc.1*
%{_mandir}/man1/vncpasswd.1*
%{_mandir}/man1/vncconfig.1*

%files server-module
%{_libdir}/xorg/modules/extensions/libvnc.so
%config %{_sysconfdir}/X11/xorg.conf.d/10-libvnc.conf

%files server-applet
%doc java/com/tigervnc/vncviewer/README
%{_datadir}/vnc/classes/*

%files license
%license LICENCE.TXT

%files icons
%{_datadir}/icons/hicolor/*/apps/*

%changelog
* Wed Jul 18 2018 openEuler Buildteam <buildteam@openeuler.org> - 1.9.0-4
- Package init
