# Maintainer: Juliette Monsel <j_4321@protonmail.com>
pkgname=tkeditor
pkgver=1.0.1
pkgrel=1
pkgdesc="Python IDE"
arch=('any')
license=('GPL3')
makedepends=('python-setuptools')
depends=('tk'
         'desktop-file-utils'
         'python-screeninfo'
         'python-tkfilebrowser'
         'python-pyflakes'
         'python-pygments'
         'python-pycodestyle')
source=("$pkgname-$pkgver.tar.gz")
sha512sums=('d4c509e90618c5683728f55c961beb062032946a2a2954f5a5c683e69048a24172db0405b1694724b3590df71a2b1648cb91d9acd6c1340c77e63f421c1936ce')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py build
}
package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --prefix=/usr --optimize=1 --skip-build
}
