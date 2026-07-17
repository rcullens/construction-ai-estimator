"""
Default standard trade definitions.
These are loaded as the starting point. Users can rename display_name,
deactivate, or add fully custom trades on top of this list.
"""

from models.models import TradeDefinition, TradeCode, CSIDivision

DEFAULT_TRADE_DEFINITIONS: list[TradeDefinition] = [
    TradeDefinition(
        code=TradeCode.GENERAL,
        display_name="General Requirements / Conditions",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_00, CSIDivision.DIV_01],
        description="General conditions, temporary facilities, project management, and overall requirements",
        sort_order=10
    ),
    TradeDefinition(
        code=TradeCode.DEMOLITION,
        display_name="Demolition / Existing Conditions",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_02],
        description="Selective demolition, abatement, and existing conditions work",
        sort_order=20
    ),
    TradeDefinition(
        code=TradeCode.EARTHWORK,
        display_name="Earthwork / Civil",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_31],
        description="Excavation, grading, site preparation, and earthwork",
        sort_order=30
    ),
    TradeDefinition(
        code=TradeCode.UTILITIES,
        display_name="Utilities",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_33],
        description="Site utilities, water, sewer, storm, and related infrastructure",
        sort_order=40
    ),
    TradeDefinition(
        code=TradeCode.EXTERIOR_IMPROVEMENTS,
        display_name="Exterior Improvements",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_32],
        description="Paving, landscaping, fencing, site furnishings, and exterior improvements",
        sort_order=50
    ),
    TradeDefinition(
        code=TradeCode.CONCRETE,
        display_name="Concrete",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_03],
        description="Cast-in-place concrete, precast, reinforcing, and concrete-related work",
        sort_order=60
    ),
    TradeDefinition(
        code=TradeCode.MASONRY,
        display_name="Masonry",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_04],
        description="Brick, block, stone, and masonry work",
        sort_order=70
    ),
    TradeDefinition(
        code=TradeCode.STRUCTURAL_STEEL,
        display_name="Structural Steel / Metals",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_05],
        description="Structural steel, miscellaneous metals, and metal fabrications",
        sort_order=80
    ),
    TradeDefinition(
        code=TradeCode.MILLWORK,
        display_name="Millwork",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_06],
        description="Architectural woodwork, casework, cabinets, trim, and related plastics/composites",
        sort_order=90
    ),
    TradeDefinition(
        code=TradeCode.THERMAL_MOISTURE,
        display_name="Thermal & Moisture Protection",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_07],
        description="Roofing, waterproofing, insulation, and air/vapor barriers",
        sort_order=100
    ),
    TradeDefinition(
        code=TradeCode.OPENINGS,
        display_name="Openings",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_08],
        description="Doors, frames, hardware, windows, and glazing",
        sort_order=110
    ),
    TradeDefinition(
        code=TradeCode.FINISHES,
        display_name="Finishes",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_09],
        description="Drywall, ceilings, flooring, painting, and interior finishes",
        sort_order=120
    ),
    TradeDefinition(
        code=TradeCode.SPECIALTIES,
        display_name="Specialties",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_10],
        description="Toilet accessories, signage, lockers, fire extinguishers, and specialties",
        sort_order=130
    ),
    TradeDefinition(
        code=TradeCode.EQUIPMENT,
        display_name="Equipment",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_11],
        description="Installed equipment (kitchen, lab, medical, etc.)",
        sort_order=140
    ),
    TradeDefinition(
        code=TradeCode.FURNISHINGS,
        display_name="Furnishings",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_12],
        description="Furniture, window treatments, and furnishings",
        sort_order=150
    ),
    TradeDefinition(
        code=TradeCode.SPECIAL_CONSTRUCTION,
        display_name="Special Construction",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_13],
        description="Special structures, cleanrooms, radiation protection, etc.",
        sort_order=160
    ),
    TradeDefinition(
        code=TradeCode.CONVEYING,
        display_name="Conveying Equipment",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_14],
        description="Elevators, escalators, lifts, and conveying systems",
        sort_order=170
    ),
    TradeDefinition(
        code=TradeCode.FIRE_SUPPRESSION,
        display_name="Fire Suppression",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_21],
        description="Fire sprinklers, standpipes, and fire suppression systems",
        sort_order=180
    ),
    TradeDefinition(
        code=TradeCode.PLUMBING,
        display_name="Plumbing",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_22],
        description="Plumbing fixtures, piping, and plumbing systems",
        sort_order=190
    ),
    TradeDefinition(
        code=TradeCode.HVAC,
        display_name="HVAC / Mechanical",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_23],
        description="Heating, ventilation, air conditioning, and mechanical systems",
        sort_order=200
    ),
    TradeDefinition(
        code=TradeCode.ELECTRICAL,
        display_name="Electrical",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_26],
        description="Electrical power, lighting, and related systems",
        sort_order=210
    ),
    TradeDefinition(
        code=TradeCode.COMMUNICATIONS,
        display_name="Communications / Low Voltage",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_27],
        description="Data, voice, audiovisual, and low-voltage communications",
        sort_order=220
    ),
    TradeDefinition(
        code=TradeCode.ELECTRONIC_SAFETY,
        display_name="Electronic Safety & Security",
        is_custom=False,
        csi_divisions=[CSIDivision.DIV_28],
        description="Fire alarm, access control, CCTV, and electronic security",
        sort_order=230
    ),
    TradeDefinition(
        code=TradeCode.OTHER,
        display_name="Other / Specialty",
        is_custom=False,
        csi_divisions=[],
        description="Catch-all for work that does not fit standard trades",
        sort_order=999
    ),
]
