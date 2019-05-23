# Maintainer: Juliette Monsel <j_4321 at protonmail dot com>
pkgname=tkeditor
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
sha512sums=('5940765a1e5aa9f14592d473ced762ecdabeb58ab25e4036f2c9f365846a9ba6c6fda711ecfffa641761f74030090ff47a6574b7eef50d5edb0e17af6d538a63')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py build
}
package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --prefix=/usr --optimize=1 --skip-build
}
