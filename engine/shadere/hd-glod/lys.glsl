// HD-glød, pass 0: bildet ned i en firedel av størrelsen (snitt av 4 x 4 piksler med fire
// lineære oppslag), og bare det som er lysere enn terskelen blir igjen.

#pragma parameter GLOD_TERSKEL "Glød: terskel" 0.68 0.0 1.0 0.02

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
uniform COMPAT_PRECISION float GLOD_TERSKEL;
#else
#define GLOD_TERSKEL 0.68
#endif

void main()
{
	vec2 d = 1.0 / TextureSize;
	vec3 c = COMPAT_TEXTURE(Texture, TEX0.xy + d * vec2(-1.0, -1.0)).rgb
	       + COMPAT_TEXTURE(Texture, TEX0.xy + d * vec2( 1.0, -1.0)).rgb
	       + COMPAT_TEXTURE(Texture, TEX0.xy + d * vec2(-1.0,  1.0)).rgb
	       + COMPAT_TEXTURE(Texture, TEX0.xy + d * vec2( 1.0,  1.0)).rgb;
	c *= 0.25;
	float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
	float w = smoothstep(GLOD_TERSKEL, min(1.0, GLOD_TERSKEL + 0.25), luma);
	// Lineært lys, så gløden legges til som lys og ikke som grått
	FragColor = vec4(c * c * w, 1.0);
}
#endif
