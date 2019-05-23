# Maintainer: Juliette Monsel <j_4321@protonmail.com>
pkgname=tkeditor
pkgver=1.0.1
pkgrel=2
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
         'python-pycodestyle')
source=("$pkgname-$pkgver.tar.gz")
sha512sums=('bbead729d73d2e4cf40e84162b8b0bc0686314bad855c9a8ee75ef3b4b311bf4ff50a55de03ac23def8b4ba32cd5f374fb4f8ba1ec1a876e2b23f9a455416a3a')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py build
}
package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir/" --prefix=/usr --optimize=1 --skip-build
}
