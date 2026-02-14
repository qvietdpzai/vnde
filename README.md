# VNDE (GNOME Edition)

Ban nay dung GNOME Shell nhung van hien session login ten `VNDE`.

## Da nang cap theo yeu cau
- `VN App Center`: giao dien GUI kieu app center, cai app native/snap/flatpak.
- `VN News`: ung dung doc RSS trong app (khong mo web ngay).
- `VN News CLI`: doc tin trong terminal.
- `VN Music`: giao dien GUI hien dai.
- `VN News Panel`: autostart gui thong bao headline dinh ky.
- Tat ca app VNDE co icon rieng phong cach Viet.

## Cai dat
```bash
cd "/mnt/data/vn de"
chmod +x install-vnde.sh
./install-vnde.sh --profile gnome
```

## Lenh Terminal Nhanh
Sau khi cai xong 1 lan, ban co them 2 lenh:
```bash
vnde
vnde-install
vnde-update
vnde-bootstrap
```
- `vnde`: lenh tong hop (`vnde install`, `vnde update`, `vnde menu`, `vnde terminal`, ...)
- `vnde-install`: cai/ap dung VNDE bang terminal
- `vnde-update`: cap nhat source VNDE va apply lai config
- `vnde-bootstrap`: tu clone source + cai tu dong

## Cai dat bang lenh (khong goi truc tiep install-vnde.sh)
Khi dang o thu muc source VNDE, ban co the dung:
```bash
./vnde/scripts/vnde install
```
Sau khi cai xong, dung truc tiep:
```bash
vnde install
vnde update
```

## Cai dat 1 lenh tu moi noi (khong can co thu muc vnde)
Dat URL repo qua bien moi truong (hoac dung mac dinh trong script), roi chay:
```bash
VNDE_REPO_URL="https://github.com/<org>/<repo>.git" bash -c "$(curl -fsSL https://raw.githubusercontent.com/<org>/<repo>/main/vnde/scripts/bootstrap-vnde.sh)"
```

## Dang nhap session VNDE
1. Logout
2. O login screen, chon session `VNDE`
3. Login lai

## Phim tat
- `Super + Space`: VN Menu
- `Super + A`: VN App Center
- `Super + N`: VN News (GUI)
- `Super + Shift + N`: VN News CLI (Terminal)
- `Super + M`: VN Music
- `Print`: Flameshot

## Ghi chu
- Neu dang o KDE/Openbox, hay login vao GNOME truoc roi chay:
```bash
./install-vnde.sh --profile gnome --no-packages
```
- Neu can ban cu openbox:
```bash
./install-vnde.sh --profile openbox
```
