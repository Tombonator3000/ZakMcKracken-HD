// Måling av den varmeste løkken i DigHD::compose() (romkilden) med ScummVMs egen
// Graphics::PixelFormat, mot en versjon som gjør valgene én gang per originalpiksel
// og bruker en tabell per palettindeks. Ikke en del av motoren.
//
// Bygg fra engine/scummvm etter engine/build.sh (bruker ScummVMs egne hoder):
//   g++ -O2 -std=c++17 -DSDL_BACKEND -DUSE_SDL2 -DPOSIX $(sdl2-config --cflags) -I. -I./engines \
//       ../../tools/ytelse/compose_bench.cpp common/libcommon.a -o /tmp/compose_bench
// Kjør: /tmp/compose_bench [antall runder, standard 40]
// Resultat 14. oktober 2026 (Xeon 2,8 GHz, én tråd): vanlig palett 12 ms mot 0,6 ms,
// nedtoning 25 ms mot 9 ms, 0 ulike byte. Se docs/MOTOR-FORBEDRING.md.
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#define FORBIDDEN_SYMBOL_ALLOW_ALL
#include "graphics/pixelformat.h"

typedef unsigned char u8;
typedef unsigned int u32;

static const int W = 320, H = 240, N = 4;  // Zak FM-Towns: 320 x 240, HD i 4x
static const int RW = 960, RH = 128;        // et bredt rom

struct Setup {
	Graphics::PixelFormat rgba = Graphics::PixelFormat::createFormatRGBA32();
	Graphics::PixelFormat fmt = Graphics::PixelFormat::createFormatRGBA32();  // skjermen DigHD får (32 bit)
	u8 pal[768], basePal[768];
	std::vector<u8> idxImg;       // RW x RH
	std::vector<u32> hdImg;       // RW*N x RH*N
	std::vector<u8> shadow;       // W x H (verdien på skjermen)
	std::vector<int> srcX, srcY;  // romkoordinat per skjermpiksel
	std::vector<u8> out;          // W*N x H*N x 4
};

// Slik tinted() står i dighd.cpp (kalt for hver av de 16 underpikslene)
static inline u32 tintedOld(const Setup &s, u32 rgba, u8 idx) {
	u8 a, r, g, b;
	s.rgba.colorToARGB(rgba, a, r, g, b);
	const u8 *cur = s.pal + idx * 3;
	const u8 *base = s.basePal + idx * 3;
	if (cur[0] == base[0] && cur[1] == base[1] && cur[2] == base[2])
		return s.fmt.RGBToColor(r, g, b);
	int c[3] = { r, g, b };
	for (int k = 0; k < 3; k++)
		c[k] = base[k] ? std::min(255, c[k] * cur[k] / base[k]) : cur[k];
	return s.fmt.RGBToColor(c[0], c[1], c[2]);
}

static void composeOld(Setup &s) {
	const int bpp = 4, outPitch = W * N * bpp;
	for (int sy = 0; sy < H; sy++) {
		for (int sx = 0; sx < W; sx++) {
			const u8 idx = s.shadow[sy * W + sx];
			const int ix = s.srcX[sy * W + sx], iy = s.srcY[sy * W + sx];
			u8 *out = s.out.data() + (sy * N) * outPitch + (sx * N) * bpp;
			for (int dy = 0; dy < N; dy++) {
				u8 *o = out + dy * outPitch;
				const u32 *t = s.hdImg.data() + (size_t)(iy * N + dy) * RW * N + ix * N;
				for (int dx = 0; dx < N; dx++, o += bpp) {
					const u32 col = tintedOld(s, t[dx], idx);
					memcpy(o, &col, 4);
				}
			}
		}
	}
}

// Forslaget: per palettindeks, når paletten endres: uendret (kopi) eller faktor i 8.8 fast komma.
// Per originalpiksel: ett oppslag. Uendret farge og samme format som HD-bildet: kopier 4 piksler.
struct Tint {
	u8 same[256];
	int mul[256][3];   // ny/gammel * 256, -1 = kanalen var svart (ta ny verdi)
	u8 cur[256][3];
};

static void makeTint(const Setup &s, Tint &t) {
	for (int k = 0; k < 256; k++) {
		const u8 *cur = s.pal + k * 3, *base = s.basePal + k * 3;
		t.same[k] = cur[0] == base[0] && cur[1] == base[1] && cur[2] == base[2];
		for (int ch = 0; ch < 3; ch++) {
			t.mul[k][ch] = base[ch] ? (int)(((cur[ch] << 16) + base[ch] - 1) / base[ch]) : -1;
			t.cur[k][ch] = cur[ch];
		}
	}
}

static void composeNew(Setup &s, const Tint &t) {
	const int bpp = 4, outPitch = W * N * bpp;
	const bool sameFmt = s.fmt == s.rgba;  // i praksis alltid for 32-biters skjerm
	const int rs = s.rgba.rShift, gs = s.rgba.gShift, bs = s.rgba.bShift;
	const int ors = s.fmt.rShift, ogs = s.fmt.gShift, obs = s.fmt.bShift;
	const u32 alpha = s.fmt.ARGBToColor(255, 0, 0, 0);
	for (int sy = 0; sy < H; sy++) {
		for (int sx = 0; sx < W; sx++) {
			const u8 idx = s.shadow[sy * W + sx];
			const int ix = s.srcX[sy * W + sx], iy = s.srcY[sy * W + sx];
			u8 *out = s.out.data() + (sy * N) * outPitch + (sx * N) * bpp;
			const u32 *t0 = s.hdImg.data() + (size_t)(iy * N) * RW * N + ix * N;
			if (t.same[idx] && sameFmt) {
				for (int dy = 0; dy < N; dy++)
					memcpy(out + dy * outPitch, t0 + (size_t)dy * RW * N, N * 4);
				continue;
			}
			const int *m = t.mul[idx];
			const u8 *cur = t.cur[idx];
			for (int dy = 0; dy < N; dy++) {
				u32 *o = (u32 *)(out + dy * outPitch);
				const u32 *tp = t0 + (size_t)dy * RW * N;
				for (int dx = 0; dx < N; dx++) {
					const u32 c = tp[dx];
					int r = (c >> rs) & 0xFF, g = (c >> gs) & 0xFF, b = (c >> bs) & 0xFF;
					if (!t.same[idx]) {
						r = m[0] < 0 ? cur[0] : std::min(255, (int)((unsigned)r * m[0] >> 16));
						g = m[1] < 0 ? cur[1] : std::min(255, (int)((unsigned)g * m[1] >> 16));
						b = m[2] < 0 ? cur[2] : std::min(255, (int)((unsigned)b * m[2] >> 16));
					}
					o[dx] = alpha | ((u32)r << ors) | ((u32)g << ogs) | ((u32)b << obs);
				}
			}
		}
	}
}

static double ms(std::chrono::steady_clock::duration d) {
	return std::chrono::duration<double, std::milli>(d).count();
}

int main(int argc, char **argv) {
	const int reps = argc > 1 ? atoi(argv[1]) : 40;
	Setup s;
	srand(1);
	for (int i = 0; i < 768; i++)
		s.basePal[i] = s.pal[i] = (u8)(rand() & 0xFF);
	s.idxImg.resize(RW * RH);
	for (auto &v : s.idxImg)
		v = (u8)(rand() & 0xFF);
	s.hdImg.resize((size_t)RW * N * RH * N);
	for (auto &v : s.hdImg)
		v = (u32)rand() | 0xFF000000u;
	s.shadow.resize(W * H);
	s.srcX.resize(W * H);
	s.srcY.resize(W * H);
	for (int y = 0; y < H; y++)
		for (int x = 0; x < W; x++) {
			const int rx = (x + 200) % RW, ry = y % RH;
			s.srcX[y * W + x] = rx;
			s.srcY[y * W + x] = ry;
			s.shadow[y * W + x] = s.idxImg[ry * RW + rx];
		}
	s.out.resize((size_t)W * N * H * N * 4);
	std::vector<u8> ref(s.out.size());

	Tint t;
	for (int pass = 0; pass < 2; pass++) {
		if (pass == 1) {
			// Nedtoning: alle farger 60 prosent
			for (int i = 0; i < 768; i++)
				s.pal[i] = (u8)(s.basePal[i] * 6 / 10);
		}
		makeTint(s, t);
		composeOld(s);
		memcpy(ref.data(), s.out.data(), ref.size());
		composeNew(s, t);
		size_t diff = 0;
		for (size_t i = 0; i < ref.size(); i++)
			diff += ref[i] != s.out[i];

		auto a = std::chrono::steady_clock::now();
		for (int i = 0; i < reps; i++)
			composeOld(s);
		auto b = std::chrono::steady_clock::now();
		for (int i = 0; i < reps; i++) {
			makeTint(s, t);
			composeNew(s, t);
		}
		auto c = std::chrono::steady_clock::now();
		printf("%s: hele skjermen (1280 x 960) i dag %.2f ms, forslag %.2f ms, %.1f ganger raskere, ulike byte: %zu\n",
		       pass ? "nedtoning" : "vanlig palett", ms(b - a) / reps, ms(c - b) / reps, ms(b - a) / ms(c - b), diff);
	}
	return 0;
}
