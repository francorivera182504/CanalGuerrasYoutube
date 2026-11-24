import bpy
NF=200
SEED=[1]
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    return m, nt, nt.nodes["Material Output"]

def vol_mat(name, col, dens, emit=0.0, ecol=None, noise_scale=2.5):
    """Volumen suave: densidad = falloff radial × ruido (las instancias son esferas de radio 1)."""
    m, nt, out = node_mat(name); N = nt.nodes.new; Lk = nt.links.new
    pv = N("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1)
    if emit:
        pv.inputs["Emission Strength"].default_value = emit; pv.inputs["Emission Color"].default_value = (*(ecol or col), 1)
    tc = N("ShaderNodeTexCoord"); ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    mr = N("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 1.0; mr.inputs["From Max"].default_value = 0.2
    nz = N("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 6
    m1 = N("ShaderNodeMath"); m1.operation = "MULTIPLY"; m2 = N("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = dens
    pw = N("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
    Lk(tc.outputs["Object"], ln.inputs[0]); Lk(ln.outputs["Value"], mr.inputs["Value"])
    Lk(tc.outputs["Object"], nz.inputs["Vector"]); Lk(nz.outputs["Fac"], pw.inputs[0])
    Lk(mr.outputs["Result"], m1.inputs[0]); Lk(pw.outputs["Value"], m1.inputs[1]); Lk(m1.outputs["Value"], m2.inputs[0])
    fv = N("ShaderNodeValue"); fv.name = "Fade"; fv.outputs[0].default_value = 1.0
    m3 = N("ShaderNodeMath"); m3.operation = "MULTIPLY"; Lk(m2.outputs["Value"], m3.inputs[0]); Lk(fv.outputs[0], m3.inputs[1])
    Lk(m3.outputs["Value"], pv.inputs["Density"]); Lk(pv.outputs["Volume"], out.inputs["Volume"])
    if emit:   # la emisión del Principled Volume no depende de la densidad: hay que multiplicarla
        me = N("ShaderNodeMath"); me.operation = "MULTIPLY"; me.inputs[1].default_value = emit / max(dens, 1e-3)
        Lk(m3.outputs["Value"], me.inputs[0]); Lk(me.outputs[0], pv.inputs["Emission Strength"])
    return m
def emitter(name, loc, sx, sy, parent=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = (sx, sy, 1)
    o.show_instancer_for_render = False; o.show_instancer_for_viewport = False
    if parent: o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o

SEED = [1]
def psys(o, ins, count, f0, f1, life, vel, rnd, size, srand=0.6, grav=1.0, drag=0.0, up=0.0, spin=True, lrand=0.4):
    o.modifiers.new("ps%d" % SEED[0], "PARTICLE_SYSTEM"); p = o.particle_systems[-1]; p.seed = SEED[0]; SEED[0] += 1
    s = p.settings; s.count = int(count); s.frame_start = f0; s.frame_end = max(f0 + 0.01, f1)
    s.lifetime = life; s.lifetime_random = lrand; s.emit_from = "FACE"; s.use_emit_random = True
    s.normal_factor = vel; s.factor_random = rnd; s.object_align_factor = (0, 0, up)
    s.render_type = "OBJECT"; s.instance_object = ins; s.particle_size = size; s.size_random = srand
    s.physics_type = "NEWTON"; s.effector_weights.gravity = grav; s.drag_factor = drag; s.display_method = "DOT"
    if spin:
        s.use_rotations = True; s.rotation_mode = "NONE"; s.phase_factor_random = 2.0
        s.angular_velocity_mode = "RAND"; s.angular_velocity_factor = 4.0
    return s

def vol_shape(name, loc, dens, col, shape="ball", emit=0.0, ecol=(1.0, 0.4, 0.08), taper=(0.5, 0.5), ptop=1.0,
              speed=0.0, nscale=1.2, stretch=(1, 1, 1), dens_keys=None, emit_keys=None, scale_keys=None, parent=None, gate=(0.38, 3.2)):
    """Volumen procedural (Eevee). shape='ball' (elipsoide) o 'column' (columna que se abre o afina con la altura).
    Densidad = máscara × ruido 4D que sube; la emisión se multiplica por la máscara (si no, ilumina toda la caja)."""
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc); d = bpy.context.object; d.name = name
    if parent: d.parent = parent; d.matrix_parent_inverse = parent.matrix_world.inverted()
    m, nt, out = node_mat(name + "M"); N = nt.nodes.new; Lk = nt.links.new
    def mth(op, a_=None, b_=None, clamp=False, c_=None):
        n = N("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i_, v_ in enumerate((a_, b_, c_)):
            if v_ is None: continue
            if isinstance(v_, (int, float)): n.inputs[i_].default_value = v_
            else: Lk(v_, n.inputs[i_])
        return n.outputs[0]
    tc = N("ShaderNodeTexCoord"); ob = tc.outputs["Object"]
    sp = N("ShaderNodeSeparateXYZ"); Lk(ob, sp.inputs[0]); X, Y, Z = sp.outputs[0], sp.outputs[1], sp.outputs[2]
    if shape == "ball":
        ln = N("ShaderNodeVectorMath"); ln.operation = "LENGTH"; Lk(ob, ln.inputs[0])
        mask = mth("POWER", mth("SUBTRACT", 1.0, ln.outputs["Value"], True), 1.8)
    else:
        h = mth("MULTIPLY_ADD", Z, 0.5, False, 0.5)                      # 0 abajo, 1 arriba
        tap = mth("MULTIPLY_ADD", h, taper[1], False, taper[0])
        r = mth("DIVIDE", mth("SQRT", mth("ADD", mth("MULTIPLY", X, X), mth("MULTIPLY", Y, Y))), tap)
        mr = mth("POWER", mth("SUBTRACT", 1.0, r, True), 1.5)
        top = mth("POWER", mth("SUBTRACT", 1.0, h, True), ptop)
        bot = mth("MULTIPLY", h, 6.0, True)
        mask = mth("MULTIPLY", mth("MULTIPLY", mr, top), bot)
    st_ = N("ShaderNodeVectorMath"); st_.operation = "MULTIPLY"; st_.inputs[1].default_value = stretch; Lk(ob, st_.inputs[0])
    off = N("ShaderNodeVectorMath"); off.operation = "ADD"; Lk(st_.outputs["Vector"], off.inputs[0])
    nz = N("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = nscale
    nz.inputs["Detail"].default_value = 10; nz.inputs["Roughness"].default_value = 0.62; Lk(off.outputs["Vector"], nz.inputs["Vector"])
    g = mth("MULTIPLY_ADD", nz.outputs["Fac"], gate[1], True, -gate[0] * gate[1])
    mg = mth("MULTIPLY", mask, g)
    fv = N("ShaderNodeValue"); dv = mth("MULTIPLY", mth("MULTIPLY", mg, dens), fv.outputs[0])
    pv = N("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1); Lk(dv, pv.inputs["Density"])
    if emit:
        ev_ = N("ShaderNodeValue"); pv.inputs["Emission Color"].default_value = (*ecol, 1)
        Lk(mth("MULTIPLY", mg, ev_.outputs[0]), pv.inputs["Emission Strength"])
        for f, v in (emit_keys or ((1, emit),)): ev_.outputs[0].default_value = v; ev_.outputs[0].keyframe_insert("default_value", frame=f)
    Lk(pv.outputs["Volume"], out.inputs["Volume"]); d.data.materials.append(m)
    for f, v in (dens_keys or ((1, 1.0),)): fv.outputs[0].default_value = v; fv.outputs[0].keyframe_insert("default_value", frame=f)
    off.inputs[1].default_value = (0, 0, 0); off.inputs[1].keyframe_insert("default_value", frame=1)
    off.inputs[1].default_value = (0, 0, -speed * NF / 30); off.inputs[1].keyframe_insert("default_value", frame=NF)
    nz.inputs["W"].default_value = 0; nz.inputs["W"].keyframe_insert("default_value", frame=1)
    nz.inputs["W"].default_value = NF / 30 * 0.8; nz.inputs["W"].keyframe_insert("default_value", frame=NF)
    for f, sz in (scale_keys or ()): d.scale = sz; d.keyframe_insert("scale", frame=f)
    return d


