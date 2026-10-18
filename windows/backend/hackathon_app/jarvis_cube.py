import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=3.0, location=(0, 0, 1.5))
obj = bpy.context.active_object
mat = bpy.data.materials.new(name="cube_Mat")
mat.use_nodes = True
p = mat.node_tree.nodes.get("Principled BSDF")
if p:
    p.inputs["Base Color"].default_value = (0.1, 0.7, 0.9, 1.0)
    p.inputs["Metallic"].default_value = 0.8
    p.inputs["Roughness"].default_value = 0.2
obj.data.materials.append(mat)
bpy.ops.object.camera_add(location=(6, -6, 5), rotation=(1.1, 0, 0.8))
bpy.context.scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='SUN', location=(5, -3, 7))
print("Model 'cube' generated successfully.")
