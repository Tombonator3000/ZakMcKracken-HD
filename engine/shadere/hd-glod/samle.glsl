// HD-glød, siste pass: originalbildet (Orig) med gløden fra pass 2 lagt til som lys,
// så vignett, metning og kontrast. Alt er svakt som standard; HD-tegningene skal se ut
// som de er tegnet, bare med litt lys rundt lamper, skjermer og himmel.

#pragma parameter GLOD_STYRKE "Glød: styrke" 0.30 0.0 1.5 0.05
#pragma parameter VIGNETT "Vignett" 0.22 0.0 1.0 0.02
#pragma parameter METNING "Metning" 1.04 0.5 1.5 0.02
#pragma parameter KONTRAST "Kontrast" 1.03 0.8 1.3 0.01

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
uniform COMPAT_PRECISION vec2 InputSize;
uniform COMPAT_PRECISION vec2 OrigTextureSize;
uniform COMPAT_PRECISION vec2 OrigInputSize;
uniform sampler2D Texture;
uniform sampler2D OrigTexture;
COMPAT_VARYING vec4 TEX0;
#ifdef PARAMETER_UNIFORM
uniform COMPAT_PRECISION float GLOD_STYRKE;
uniform COMPAT_PRECISION float VIGNETT;
uniform COMPAT_PRECISION float METNING;
uniform COMPAT_PRECISION float KONTRAST;
#else
#define GLOD_STYRKE 0.30
#define VIGNETT 0.22
#define METNING 1.04
#define KONTRAST 1.03
#endif

void main()
{
	// Samme sted i bildet, regnet om for hver tekstur (de kan ha ulik utfylling)
	vec2 p = TEX0.xy * TextureSize / InputSize;
	vec3 orig = COMPAT_TEXTURE(OrigTexture, p * OrigInputSize / OrigTextureSize).rgb;
	vec3 glod = COMPAT_TEXTURE(Texture, TEX0.xy).rgb;

	vec3 lin = orig * orig + GLOD_STYRKE * glod;
	vec3 c = sqrt(clamp(lin, 0.0, 1.0));

	float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(vec3(luma), c, METNING);
	c = (c - 0.5) * KONTRAST + 0.5;

	vec2 v = p - 0.5;
	c *= 1.0 - VIGNETT * smoothstep(0.18, 0.62, dot(v, v) * 1.6);

	FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
#endif
