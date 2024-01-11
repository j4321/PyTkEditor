# Maintainer: Juliette Monsel <j_4321 at protonmail dot com>
pkgname=pytkeditor-git
pkgver=r288.a072cc5
pkgrel=1
pkgdesc="Python IDE"
arch=('any')
license=('GPL3')
makedepends=('python-setuptools')
depends=('tk'
         'desktop-file-utils'
         'python-pillow'
         'python-xlib'
         'python-jedi>=0.16.0'
         'python-docutils'
         'python-tkfilebrowser'
         'python-tkcolorpicker'
         'python-pyflakes'
         'python-pygments'
         'python-ewmh'
         'python-xhtml2pdf'
         'python-pycups'
         'python-pycodestyle')
optdepends=('python-qtconsole: Run code in Jupyter QtConsole')
source=("${pkgname}::git+https://gitlab.com/j_4321/PyTkEditor#branch=dev")
sha512sums=('SKIP')

pkgver() {
  cd "$pkgname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "$srcdir/$pkgname"
    python setup.py build
}

package() {
    cd "$srcdir/$pkgname"
    python setup.py install --root="$pkgdir/" --prefix=/usr --optimize=1 --skip-build
}

