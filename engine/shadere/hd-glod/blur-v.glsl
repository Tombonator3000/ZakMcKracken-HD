// HD-glød: gaussisk uskarphet vannrett (9 punkter med fem lineære oppslag).

#pragma parameter GLOD_BREDDE "Glød: bredde" 1.6 0.5 4.0 0.1

#if defined(VERTEX)
#if __VERSION__ >= 130
#define COMPAT_VARYING out
#define COMPAT_ATTRIBUTE in
#else
#define COMPAT_VARYING varying
#define COMPAT_ATTRIBUTE attribute
#endif
COMPAT_ATTRIBUTE vec4 VertexCoord;
COMPAT_ATTRIBUTE vec4 TexCoord;
COMPAT_VARYING vec4 TEX0;
uniform mat4 MVPMatrix;
void main()
{
	gl_Position = MVPMatrix * VertexCoord;
	TEX0.xy = TexCoord.xy;
}
#elif defined(FRAGMENT)
#if __VERSION__ >= 130
#define COMPAT_VARYING in
#define COMPAT_TEXTURE texture
out vec4 FragColor;
#else
#define COMPAT_VARYING varying
#define FragColor gl_FragColor
#define COMPAT_TEXTURE texture2D
#endif
#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
#endif
uniform COMPAT_PRECISION vec2 TextureSize;
uniform sampler2D Texture;
COMPAT_VARYING vec4 TEX0;
#ifdef PARAMETER_UNIFORM
uniform COMPAT_PRECISION float GLOD_BREDDE;
#else
#define GLOD_BREDDE 1.6
#endif

void main()
{
	vec2 d = vec2(1.0, 0.0) * GLOD_BREDDE / TextureSize;
	vec3 c = COMPAT_TEXTURE(Texture, TEX0.xy).rgb * 0.2270270;
	c += (COMPAT_TEXTURE(Texture, TEX0.xy + d * 1.3846154).rgb + COMPAT_TEXTURE(Texture, TEX0.xy - d * 1.3846154).rgb) * 0.3162162;
	c += (COMPAT_TEXTURE(Texture, TEX0.xy + d * 3.2307692).rgb + COMPAT_TEXTURE(Texture, TEX0.xy - d * 3.2307692).rgb) * 0.0702703;
	FragColor = vec4(c, 1.0);
}
#endif
