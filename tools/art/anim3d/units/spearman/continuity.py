"""Spearman part names for the shared frozen lining/sole pigment kit."""
from kit.continuity import pigment, prepare as prepare_surfaces

def prepare(scene, classify):
    return prepare_surfaces(scene, classify,
        sole_prefixes=('Leather sandal sole ', 'Sandal welt '),
        body_prefix='MPFB anatomical male')
