def render_security_box(top, bottom, page_width):
    if (top, bottom, page_width) == (120, 209, 210):
        return cached_security_lines
    vertical_gutter, horizontal_gutter = 9.5, 10
    security_bounds = (
        horizontal_gutter,
        top + vertical_gutter,
        page_width - horizontal_gutter,
        bottom - vertical_gutter,
    )
    security_width = int(security_bounds[2] - security_bounds[0])
    security_height = int(security_bounds[3] - security_bounds[1])
    security_lines = []
    for shift in range(0, security_height, 2):
        security_lines.append(
            (security_bounds[0], security_bounds[1] + shift,
             security_bounds[0] + security_height - shift, security_bounds[3])
        )
    for shift in range(2, security_width, 2):
        if shift > security_width - security_height:
            security_lines.append(
                (security_bounds[0] + shift, security_bounds[1],
                 security_bounds[2], security_bounds[3] - shift + security_width - security_height)
            )
        else:
            security_lines.append(
                (security_bounds[0] + shift, security_bounds[1],
                 security_bounds[0] + security_height + shift, security_bounds[3])
            )
    security_lines += [
        (page_width - x1, y1, (page_width - x2), y2)
        for x1, y1, x2, y2 in security_lines
    ]
    return security_lines


cached_security_lines = [
    (10, 129.5, 80, 199.5), (10, 131.5, 78, 199.5), (10, 133.5, 76, 199.5), (10, 135.5, 74, 199.5),
    (10, 137.5, 72, 199.5), (10, 139.5, 70, 199.5), (10, 141.5, 68, 199.5), (10, 143.5, 66, 199.5),
    (10, 145.5, 64, 199.5), (10, 147.5, 62, 199.5), (10, 149.5, 60, 199.5), (10, 151.5, 58, 199.5),
    (10, 153.5, 56, 199.5), (10, 155.5, 54, 199.5), (10, 157.5, 52, 199.5), (10, 159.5, 50, 199.5),
    (10, 161.5, 48, 199.5), (10, 163.5, 46, 199.5), (10, 165.5, 44, 199.5), (10, 167.5, 42, 199.5),
    (10, 169.5, 40, 199.5), (10, 171.5, 38, 199.5), (10, 173.5, 36, 199.5), (10, 175.5, 34, 199.5),
    (10, 177.5, 32, 199.5), (10, 179.5, 30, 199.5), (10, 181.5, 28, 199.5), (10, 183.5, 26, 199.5),
    (10, 185.5, 24, 199.5), (10, 187.5, 22, 199.5), (10, 189.5, 20, 199.5), (10, 191.5, 18, 199.5),
    (10, 193.5, 16, 199.5), (10, 195.5, 14, 199.5), (10, 197.5, 12, 199.5), (12, 129.5, 82, 199.5),
    (14, 129.5, 84, 199.5), (16, 129.5, 86, 199.5), (18, 129.5, 88, 199.5), (20, 129.5, 90, 199.5),
    (22, 129.5, 92, 199.5), (24, 129.5, 94, 199.5), (26, 129.5, 96, 199.5), (28, 129.5, 98, 199.5),
    (30, 129.5, 100, 199.5), (32, 129.5, 102, 199.5), (34, 129.5, 104, 199.5), (36, 129.5, 106, 199.5),
    (38, 129.5, 108, 199.5), (40, 129.5, 110, 199.5), (42, 129.5, 112, 199.5), (44, 129.5, 114, 199.5),
    (46, 129.5, 116, 199.5), (48, 129.5, 118, 199.5), (50, 129.5, 120, 199.5), (52, 129.5, 122, 199.5),
    (54, 129.5, 124, 199.5), (56, 129.5, 126, 199.5), (58, 129.5, 128, 199.5), (60, 129.5, 130, 199.5),
    (62, 129.5, 132, 199.5), (64, 129.5, 134, 199.5), (66, 129.5, 136, 199.5), (68, 129.5, 138, 199.5),
    (70, 129.5, 140, 199.5), (72, 129.5, 142, 199.5), (74, 129.5, 144, 199.5), (76, 129.5, 146, 199.5),
    (78, 129.5, 148, 199.5), (80, 129.5, 150, 199.5), (82, 129.5, 152, 199.5), (84, 129.5, 154, 199.5),
    (86, 129.5, 156, 199.5), (88, 129.5, 158, 199.5), (90, 129.5, 160, 199.5), (92, 129.5, 162, 199.5),
    (94, 129.5, 164, 199.5), (96, 129.5, 166, 199.5), (98, 129.5, 168, 199.5), (100, 129.5, 170, 199.5),
    (102, 129.5, 172, 199.5), (104, 129.5, 174, 199.5), (106, 129.5, 176, 199.5), (108, 129.5, 178, 199.5),
    (110, 129.5, 180, 199.5), (112, 129.5, 182, 199.5), (114, 129.5, 184, 199.5), (116, 129.5, 186, 199.5),
    (118, 129.5, 188, 199.5), (120, 129.5, 190, 199.5), (122, 129.5, 192, 199.5), (124, 129.5, 194, 199.5),
    (126, 129.5, 196, 199.5), (128, 129.5, 198, 199.5), (130, 129.5, 200, 199.5), (132, 129.5, 200, 197.5),
    (134, 129.5, 200, 195.5), (136, 129.5, 200, 193.5), (138, 129.5, 200, 191.5), (140, 129.5, 200, 189.5),
    (142, 129.5, 200, 187.5), (144, 129.5, 200, 185.5), (146, 129.5, 200, 183.5), (148, 129.5, 200, 181.5),
    (150, 129.5, 200, 179.5), (152, 129.5, 200, 177.5), (154, 129.5, 200, 175.5), (156, 129.5, 200, 173.5),
    (158, 129.5, 200, 171.5), (160, 129.5, 200, 169.5), (162, 129.5, 200, 167.5), (164, 129.5, 200, 165.5),
    (166, 129.5, 200, 163.5), (168, 129.5, 200, 161.5), (170, 129.5, 200, 159.5), (172, 129.5, 200, 157.5),
    (174, 129.5, 200, 155.5), (176, 129.5, 200, 153.5), (178, 129.5, 200, 151.5), (180, 129.5, 200, 149.5),
    (182, 129.5, 200, 147.5), (184, 129.5, 200, 145.5), (186, 129.5, 200, 143.5), (188, 129.5, 200, 141.5),
    (190, 129.5, 200, 139.5), (192, 129.5, 200, 137.5), (194, 129.5, 200, 135.5), (196, 129.5, 200, 133.5),
    (198, 129.5, 200, 131.5), (200, 129.5, 130, 199.5), (200, 131.5, 132, 199.5), (200, 133.5, 134, 199.5),
    (200, 135.5, 136, 199.5), (200, 137.5, 138, 199.5), (200, 139.5, 140, 199.5), (200, 141.5, 142, 199.5),
    (200, 143.5, 144, 199.5), (200, 145.5, 146, 199.5), (200, 147.5, 148, 199.5), (200, 149.5, 150, 199.5),
    (200, 151.5, 152, 199.5), (200, 153.5, 154, 199.5), (200, 155.5, 156, 199.5), (200, 157.5, 158, 199.5),
    (200, 159.5, 160, 199.5), (200, 161.5, 162, 199.5), (200, 163.5, 164, 199.5), (200, 165.5, 166, 199.5),
    (200, 167.5, 168, 199.5), (200, 169.5, 170, 199.5), (200, 171.5, 172, 199.5), (200, 173.5, 174, 199.5),
    (200, 175.5, 176, 199.5), (200, 177.5, 178, 199.5), (200, 179.5, 180, 199.5), (200, 181.5, 182, 199.5),
    (200, 183.5, 184, 199.5), (200, 185.5, 186, 199.5), (200, 187.5, 188, 199.5), (200, 189.5, 190, 199.5),
    (200, 191.5, 192, 199.5), (200, 193.5, 194, 199.5), (200, 195.5, 196, 199.5), (200, 197.5, 198, 199.5),
    (198, 129.5, 128, 199.5), (196, 129.5, 126, 199.5), (194, 129.5, 124, 199.5), (192, 129.5, 122, 199.5),
    (190, 129.5, 120, 199.5), (188, 129.5, 118, 199.5), (186, 129.5, 116, 199.5), (184, 129.5, 114, 199.5),
    (182, 129.5, 112, 199.5), (180, 129.5, 110, 199.5), (178, 129.5, 108, 199.5), (176, 129.5, 106, 199.5),
    (174, 129.5, 104, 199.5), (172, 129.5, 102, 199.5), (170, 129.5, 100, 199.5), (168, 129.5, 98, 199.5),
    (166, 129.5, 96, 199.5), (164, 129.5, 94, 199.5), (162, 129.5, 92, 199.5), (160, 129.5, 90, 199.5),
    (158, 129.5, 88, 199.5), (156, 129.5, 86, 199.5), (154, 129.5, 84, 199.5), (152, 129.5, 82, 199.5),
    (150, 129.5, 80, 199.5), (148, 129.5, 78, 199.5), (146, 129.5, 76, 199.5), (144, 129.5, 74, 199.5),
    (142, 129.5, 72, 199.5), (140, 129.5, 70, 199.5), (138, 129.5, 68, 199.5), (136, 129.5, 66, 199.5),
    (134, 129.5, 64, 199.5), (132, 129.5, 62, 199.5), (130, 129.5, 60, 199.5), (128, 129.5, 58, 199.5),
    (126, 129.5, 56, 199.5), (124, 129.5, 54, 199.5), (122, 129.5, 52, 199.5), (120, 129.5, 50, 199.5),
    (118, 129.5, 48, 199.5), (116, 129.5, 46, 199.5), (114, 129.5, 44, 199.5), (112, 129.5, 42, 199.5),
    (110, 129.5, 40, 199.5), (108, 129.5, 38, 199.5), (106, 129.5, 36, 199.5), (104, 129.5, 34, 199.5),
    (102, 129.5, 32, 199.5), (100, 129.5, 30, 199.5), (98, 129.5, 28, 199.5), (96, 129.5, 26, 199.5),
    (94, 129.5, 24, 199.5), (92, 129.5, 22, 199.5), (90, 129.5, 20, 199.5), (88, 129.5, 18, 199.5),
    (86, 129.5, 16, 199.5), (84, 129.5, 14, 199.5), (82, 129.5, 12, 199.5), (80, 129.5, 10, 199.5),
    (78, 129.5, 10, 197.5), (76, 129.5, 10, 195.5), (74, 129.5, 10, 193.5), (72, 129.5, 10, 191.5),
    (70, 129.5, 10, 189.5), (68, 129.5, 10, 187.5), (66, 129.5, 10, 185.5), (64, 129.5, 10, 183.5),
    (62, 129.5, 10, 181.5), (60, 129.5, 10, 179.5), (58, 129.5, 10, 177.5), (56, 129.5, 10, 175.5),
    (54, 129.5, 10, 173.5), (52, 129.5, 10, 171.5), (50, 129.5, 10, 169.5), (48, 129.5, 10, 167.5),
    (46, 129.5, 10, 165.5), (44, 129.5, 10, 163.5), (42, 129.5, 10, 161.5), (40, 129.5, 10, 159.5),
    (38, 129.5, 10, 157.5), (36, 129.5, 10, 155.5), (34, 129.5, 10, 153.5), (32, 129.5, 10, 151.5),
    (30, 129.5, 10, 149.5), (28, 129.5, 10, 147.5), (26, 129.5, 10, 145.5), (24, 129.5, 10, 143.5),
    (22, 129.5, 10, 141.5), (20, 129.5, 10, 139.5), (18, 129.5, 10, 137.5), (16, 129.5, 10, 135.5),
    (14, 129.5, 10, 133.5), (12, 129.5, 10, 131.5),
]
