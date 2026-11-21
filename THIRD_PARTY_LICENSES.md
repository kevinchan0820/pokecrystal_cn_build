# Third-party dictionary attribution for Pokémon Crystal 1.x

## Cangjie5-derived Quick full dictionary

- Project: [RIME 倉頡輸入法方案集成](https://github.com/cangjie-system/rime-cangjie-integrated)
- Source file: [cangjie.5-base.dict.yaml](https://github.com/cangjie-system/rime-cangjie-integrated/blob/dcfba770189078a2f7b347793c8e155c3c39275d/cangjie.5-base.dict.yaml)
- Pinned upstream commit: `dcfba770189078a2f7b347793c8e155c3c39275d`
- Git blob SHA1: `5b405b8e0d8b37c37a639c3a6ec06af6c52b2852`
- Scope: ONLY the upstream repository's root dictionary file; **nothing from its `resources/` directory** is imported.
- Transformation: filter to characters available in the actual game glyph map and unchanged by OpenCC s2tw, derive Quick codes from first and last Cangjie letters, preserve preferred initial candidates for audited test cases, generate ROM candidate indexes.
- Usage: code/data may be included in the legally redistributable IPS patch; copyrighted Nintendo ROM is never distributed.

The upstream repository's README states its root files are MIT unless separately noted, but `resources/` may use different licences and is excluded. The following copyright/permission notice is retained as required.

### Original MIT licence (unmodified)

```text
MIT License

Copyright (c) 2018 - 朱邦復（發明）、RIME 倉頡輸入法集成（收集整理及修訂）

All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The project must continue to check upstream provenance whenever changing the dictionary source. This notice does **not** establish the legality of sharing Nintendo's original ROM.
