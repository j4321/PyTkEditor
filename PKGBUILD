# Maintainer: Juliette Monsel <j_4321 at protonmail dot com>
pkgname=pytkeditor
pkgver=1.0.0a0
pkgrel=1
pkgdesc="Python IDE"
arch=('any')
license=('GPL3')
makedepends=('python-setuptools')
depends=('tk'
         'desktop-file-utils'
         'python-xlib'
         'python-docutils'
         'python-tkfilebrowser'
         'python-pyflakes'
         'python-pygments'
         'python-ewmh'
         'python-pillow'
         'python-jedi'
         'python-pycodestyle')
source=("$pkgname-$pkgver.tar.gz")
sha512sums=('c33a791569ddc6d3b3dc8c81316d6fd2df8d195bb2c659431241cf2f9efee10699282f908f2e201c299fe6e9cf938a45196d62d626ba25feedf1a67b05d22339')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py build
}
package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --prefix=/usr --optimize=1 --skip-build
}
