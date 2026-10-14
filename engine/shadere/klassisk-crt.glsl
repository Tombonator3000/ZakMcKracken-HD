// Klassisk CRT for Zak McKracken HD: skannlinjer, myk stråle og en svak skyggemaske.
// Skrevet for repoet (14. oktober 2026), ikke kopiert fra andre shadere.
//
// KILDEPIKSEL er hvor mange skjermpiksler én originalpiksel er i bildet ScummVM sender:
// 1 når spillet går uten HD-laget (320 x 240), 4 når HD-laget viser originalgrafikken
// i 4x (klassisk modus i DigHD). Da treffer skannlinjene originalens 240 linjer, ikke 960.

#pragma parameter KILDEPIKSEL "Skjermpiksler per originalpiksel" 1.0 1.0 8.0 1.0
#pragma parameter SKANNLINJE "Skannlinjer (styrke)" 0.55 0.0 1.0 0.05
#pragma parameter MASKE "Skyggemaske (styrke)" 0.12 0.0 0.5 0.01
#pragma parameter SKARPHET "Skarphet langs linjen" 0.65 0.0 1.0 0.05
#pragma parameter KURVE "Krumning" 0.03 0.0 0.15 0.01
#pragma parameter LYS "Lysstyrke" 1.18 0.8 1.6 0.02

#if defined(VERTEX)

#if __VERSION__ >= 130
#define COMPAT_VARYING out
#define COMPAT_ATTRIBUTE in
#else
#define COMPAT_VARYING varying
#define COMPAT_ATTRIBUTE attribute
#endif
#ifdef GL_ES
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
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

uniform COMPAT_PRECISION vec2 OutputSize;
uniform COMPAT_PRECISION vec2 TextureSize;
uniform COMPAT_PRECISION vec2 InputSize;
uniform sampler2D Texture;
COMPAT_VARYING vec4 TEX0;

#ifdef PARAMETER_UNIFORM
uniform COMPAT_PRECISION float KILDEPIKSEL;
uniform COMPAT_PRECISION float SKANNLINJE;
uniform COMPAT_PRECISION float MASKE;
uniform COMPAT_PRECISION float SKARPHET;
uniform COMPAT_PRECISION float KURVE;
uniform COMPAT_PRECISION float LYS;
#else
#define KILDEPIKSEL 1.0
#define SKANNLINJE 0.55
#define MASKE 0.12
#define SKARPHET 0.65
#define KURVE 0.03
#define LYS 1.18
#endif

// Lineært lys inn og ut, så blandingen av linjer ikke gjør bildet grått
vec3 tilLin(vec3 c) { return c * c; }
vec3 fraLin(vec3 c) { return sqrt(c); }

// Én originalpiksel (i, j) fra bildet ScummVM sender
vec3 hent(vec2 ij, vec2 orig)
{
	vec2 uv = (clamp(ij, vec2(0.0), orig - 1.0) + 0.5) / orig;
	return tilLin(COMPAT_TEXTURE(Texture, uv * InputSize / TextureSize).rgb);
}

// En rad: to nabopiksler blandet med en bratt overgang (skarp, men uten trappetrinn)
vec3 rad(float x, float j, vec2 orig)
{
	float i = floor(x - 0.5);
	float f = x - 0.5 - i;
	float k = mix(f, smoothstep(0.5 - 0.5 * SKARPHET, 0.5 + 0.5 * SKARPHET, f), SKARPHET);
	return mix(hent(vec2(i, j), orig), hent(vec2(i + 1.0, j), orig), k);
}

void main()
{
	vec2 p = TEX0.xy * TextureSize / InputSize;  // 0..1 over bildet
	// Krumning: litt tønneform
	vec2 c = p - 0.5;
	p = 0.5 + c * (1.0 + KURVE * dot(c, c) * 4.0);
	if (p.x < 0.0 || p.y < 0.0 || p.x > 1.0 || p.y > 1.0) {
		FragColor = vec4(0.0, 0.0, 0.0, 1.0);
		return;
	}

	vec2 orig = floor(InputSize / KILDEPIKSEL + 0.5);
	vec2 pos = p * orig;
	float j = floor(pos.y);
	float fy = pos.y - j - 0.5;  // -0.5..0.5 innenfor linjen

	// Strålen: linjen selv og naboen den ligger nærmest, hver med gaussisk profil.
	// Lyse linjer får bredere stråle (som et ekte rør), mørke blir tynnere.
	vec3 a = rad(pos.x, j, orig);
	float jn = fy < 0.0 ? j - 1.0 : j + 1.0;
	vec3 b = rad(pos.x, jn, orig);
	float da = abs(fy), db = 1.0 - abs(fy);
	vec3 bredA = mix(vec3(0.24), vec3(0.42), sqrt(a));
	vec3 bredB = mix(vec3(0.24), vec3(0.42), sqrt(b));
	vec3 wa = exp(-0.5 * (da * da) / (bredA * bredA));
	vec3 wb = exp(-0.5 * (db * db) / (bredB * bredB));
	vec3 strale = a * wa + b * wb;
	vec3 rett = a;
	vec3 farge = mix(rett, strale * 1.25, SKANNLINJE);

	// Skyggemaske: rød, grønn og blå stripe per tre skjermpiksler
	float m = mod(floor(gl_FragCoord.x), 3.0);
	vec3 maske = vec3(m == 0.0 ? 1.0 : 1.0 - MASKE, m == 1.0 ? 1.0 : 1.0 - MASKE, m == 2.0 ? 1.0 : 1.0 - MASKE);
	farge *= maske * LYS;

	FragColor = vec4(fraLin(clamp(farge, 0.0, 1.0)), 1.0);
}
#endif
