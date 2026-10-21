
# ---------------- LIGHTING ----------------

world=bpy.data.worlds.new("Soft studio environment") if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.48,0.50,0.54,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.4

def area_light(name,location,energy,size,target):
    bpy.ops.object.light_add(type="AREA",location=location)
    light=bpy.context.object
    light.name=name
    light.data.energy=energy
    light.data.shape="DISK"
    light.data.size=size
    aim(light,target)

area_light("Large soft key",(0,-2.5,7.0),1400,6.0,(0,0,1))
area_light("Shelf fill",(-2.5,1.2,4.0),350,2.5,(0,2,1.3))
area_light("Front fill",(4,-4,4.5),650,4.0,(0,0,1))

bpy.ops.object.light_add(type="POINT", location=(0.25,0.15,HEIGHT-0.48))
ceiling_light = bpy.context.object
ceiling_light.name = "Ceiling bulb | room light"
ceiling_light.data.energy = 180
ceiling_light.data.color = (1.0,0.78,0.52)
ceiling_light.data.shadow_soft_size = 0.18

# ---------------- DOLLHOUSE CAMERA ----------------

bpy.ops.object.camera_add(location=(0.0,-11.5,13.0))
camera=bpy.context.object
camera.name="Blender Room Preview Camera"
aim(camera,(0,0.0,0.85))
camera.data.type="ORTHO"
camera.data.ortho_scale=9.6
bpy.context.scene.camera=camera

# ---------------- RENDER FOUR LIGHTING VARIANTS ----------------
# Night renders retain subtle cool fill so walls, desk, chairs and rug stay visible.
# When lamp spots are on, their warm pools of light should clearly brighten shelves.

scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=256
scene.cycles.use_adaptive_sampling=True
scene.cycles.max_bounces=8
scene.cycles.diffuse_bounces=4
scene.cycles.glossy_bounces=4
scene.render.resolution_x=1920
scene.render.resolution_y=1440
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.cycles.use_denoising=True

# Keep the room lights separate from the three-head decorative shelf lamp.
area_light_names={"Large soft key", "Shelf fill", "Front fill", "Ceiling bulb | room light"}
lamp_light_names={f"Shelf lamp spotlight {i}" for i in (1, 2, 3)}
area_lights=[o for o in scene.objects if o.type == "LIGHT" and o.name in area_light_names]
lamp_lights=[o for o in scene.objects if o.type == "LIGHT" and o.name in lamp_light_names]
world=bpy.data.worlds.new("Soft studio environment") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world=world
world.use_nodes=True
background=world.node_tree.nodes.get("Background")


def set_render_lighting(is_day, lamps_on):
    """Four distinct moods while preserving visible detail in every render.

    Night is dim and cool, never black: low-level area lighting keeps furniture
    and room edges readable. Warm shelf spots remain the main illumination when
    the decorative lamp is enabled.
    """
    if is_day:
        # Day renders are deliberately 25% darker than the previous version,
        # so the warm shelf lamps remain visibly distinct when switched on.
        # Reduce daylight ambient and area lights only; keep lamp output unchanged.
        background.inputs["Color"].default_value = (0.68, 0.72, 0.78, 1)
        background.inputs["Strength"].default_value = 0.4125  # 25% down from 0.55
        area_energies = {"Large soft key": 1050, "Shelf fill": 262.5, "Front fill": 487.5, "Ceiling bulb | room light": 180}
    else:
        # Low cool ambient fill: night-time mood without crushing shadows to black.
        background.inputs["Color"].default_value = (0.16, 0.20, 0.30, 1)
        background.inputs["Strength"].default_value = 0.22
        area_energies = {"Large soft key": 95, "Shelf fill": 45, "Front fill": 70, "Ceiling bulb | room light": 24}

    for light in area_lights:
        light.hide_render = False
        light.data.energy = area_energies.get(light.name, light.data.energy)
        light.data.color = ((1.0, 0.78, 0.52) if light.name == "Ceiling bulb | room light" else ((1.0, 0.88, 0.72) if is_day else (0.52, 0.62, 1.0)))

    for light in lamp_lights:
        light.hide_render = not lamps_on
        # Warm spotlights have enough output to illuminate the shelf surfaces,
        # books and objects nearby, especially against the dim night ambience.
        light.data.energy = (180 if is_day else 320)
        light.data.color = (1.0, 0.70, 0.38)


# Pack imported images into the blend where possible.
try:
    bpy.ops.file.pack_all()
except Exception:
    pass

blend_path=os.path.join(OUT,"home_office_dollhouse.blend")

# Save a useful default state: daytime with the decorative lamp off.
set_render_lighting(is_day=True, lamps_on=False)
scene.render.filepath=os.path.join(OUT,"home_office_day_lights_off.png")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("\nSaved Blender project:",blend_path)
print("Rendering four lighting variants into:",OUT)

render_variants = [
    ("home_office_night_lights_off.png", False, False),
    ("home_office_night_lights_on.png",  False, True),
    ("home_office_day_lights_off.png",   True,  False),
    ("home_office_day_lights_on.png",    True,  True),
]

if AUTO_RENDER:
    for filename, is_day, lamps_on in render_variants:
        set_render_lighting(is_day, lamps_on)
        scene.render.filepath=os.path.join(OUT, filename)
        print(f"\nRendering {filename} (day={is_day}, lamps_on={lamps_on})")
        bpy.ops.render.render(write_still=True)
        print("Rendered:", scene.render.filepath)

    # Restore and save the default daylight / lamps-off state in the .blend.
    set_render_lighting(is_day=True, lamps_on=False)
    scene.render.filepath=os.path.join(OUT,"home_office_day_lights_off.png")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("\nAll four renders complete. Blender project restored to daytime / lamps off.")
else:
    print("AUTO_RENDER is disabled; no images were rendered.")
