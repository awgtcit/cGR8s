"""
Single source of truth for gamma constant seed data.
Used by both the seed script and the admin reseed route.
"""

# Format: (format, plug_length, condition, selection_criteria, value)
# condition = True  → N_tgt < 0.3
# condition = False → N_tgt >= 0.3
GAMMA_SEED_DATA = [
    # KS10SE
    ('KS10SE', 21, False, 'KS10SE,21,FALSE', 85.0),
    ('KS10SE', 21, True,  'KS10SE,21,TRUE',  95.0),
    ('KS10SE', 25, False, 'KS10SE,25,FALSE', 89.0),
    ('KS10SE', 25, True,  'KS10SE,25,TRUE',  95.0),
    ('KS10SE', 27, False, 'KS10SE,27,FALSE', 89.0),
    ('KS10SE', 27, True,  'KS10SE,27,TRUE',  95.0),
    # KS20FP
    ('KS20FP', 21, False, 'KS20FP,21,FALSE', 85.0),
    ('KS20FP', 21, True,  'KS20FP,21,TRUE',  95.0),
    ('KS20FP', 27, False, 'KS20FP,27,FALSE', 89.0),
    ('KS20FP', 27, True,  'KS20FP,27,TRUE',  95.0),
    # KS20RC
    ('KS20RC', 21, False, 'KS20RC,21,FALSE', 85.0),
    ('KS20RC', 21, True,  'KS20RC,21,TRUE',  95.0),
    ('KS20RC', 27, False, 'KS20RC,27,FALSE', 89.0),
    ('KS20RC', 27, True,  'KS20RC,27,TRUE',  95.0),
    # KS20SE
    ('KS20SE', 21, False, 'KS20SE,21,FALSE', 85.0),
    ('KS20SE', 21, True,  'KS20SE,21,TRUE',  95.0),
    ('KS20SE', 25, False, 'KS20SE,25,FALSE', 89.0),
    ('KS20SE', 25, True,  'KS20SE,25,TRUE',  95.0),
    ('KS20SE', 27, False, 'KS20SE,27,FALSE', 89.0),
    ('KS20SE', 27, True,  'KS20SE,27,TRUE',  95.0),
    # NS20DS
    ('NS20DS', 27, False, 'NS20DS,27,FALSE', 90.5),
    ('NS20DS', 27, True,  'NS20DS,27,TRUE',  90.5),
    # NS20SE
    ('NS20SE', 25, False, 'NS20SE,25,FALSE', 90.5),
    ('NS20SE', 25, True,  'NS20SE,25,TRUE',  90.5),
]

GAMMA_KNOWN_FORMATS = {row[0] for row in GAMMA_SEED_DATA}
