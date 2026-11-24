"""Render-only foot pigment and soft stone shadow, from evaluated animated feet.

The R14 'sole' flash is mostly the instep (confirmed by an object-ID pass).
Keep its frozen pigment detail; shade it as the whole foot rolls away from its
planted orientation. No pose, mesh, UV, donor rotation or saved scene changes.
"""
from kit import foot_finish as shared

ATTRIBUTE = 'Spearman foot pigment regions'
NODE_PREFIX = 'Spearman foot roll '
SIDES = ('l', 'r')

def settings(scene, cfg):
    # Keep the accepted R14 rest/held-clip shadow when the requested smaller
    # pools regress its colour metric. Host A/B exposes that alternative via
    # ground_pools=1. Move always uses compact, evaluated-sole shadows; the
    # legacy toggle permits a same-path R14 replay on the identical master.
    if scene.get('clip') != 'move':
        cfg['foot_roll'] = 0
    if cfg.get('ground_follow', 1) and (scene.get('clip') == 'move' or cfg.get('ground_pools', 0)):
        cfg.update(ground_follow=2, ground_shadow=.4, ground_back=.035,
                   ground_in=.02, ground_depth=.09, ground_width=.07,
                   base_cast=.08, base_contact=.20, contact_reach=.025)


def prepare(scene, classify):
    return shared.prepare(scene, classify, attribute=ATTRIBUTE, skin_part='skin',
        sandal_parts={s: 'sandal_'+s for s in SIDES},
        bone_groups={s: ('foot_'+s, 'ball_'+s) for s in SIDES})


def pigment(g, colour):
    return shared.pigment(g, colour, attribute=ATTRIBUTE, sides=SIDES,
                          node_prefix=NODE_PREFIX, tint=(.45, .38, .31, 1))


def update(scene):
    return shared.update(scene, rig_name='Spearman • MPFB game_engine',
        foot_bones={s: 'foot_'+s for s in SIDES},
        sole_names={s: 'Leather sandal sole '+s for s in SIDES},
        marker_names={s: 'LOOK ankle '+s for s in SIDES}, node_prefix=NODE_PREFIX)
