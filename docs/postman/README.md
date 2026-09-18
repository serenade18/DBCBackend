# Postman docs

`DBC_Backend.postman_collection.json` is generated from the live OpenAPI schema
(`openapi.yaml`), not hand-written — it always matches the actual DRF views/serializers.

## Import into Postman

1. Postman → **Import** → select `DBC_Backend.postman_collection.json`.
2. Also import `DBC_Backend_Local.postman_environment.json` and select it as your active environment
   (or just edit the collection's own `baseUrl`/`bearerToken` variables directly — both work).
3. Run **api → v1 → auth → auth register create** (or **auth login create**) once. A test script on
   that request reads the `access` token from the response and stores it in the `bearerToken`
   variable automatically — every other authenticated request already sends
   `Authorization: Bearer {{bearerToken}}`, so nothing else to configure.
4. Access tokens expire after 30 minutes — just re-run login to refresh `bearerToken`.

Not included (they return HTML/binary, not JSON, so they're outside the OpenAPI schema): the public
card page (`GET /@<slug>/`), `.vcf` download (`GET /@<slug>/contact/`), QR image
(`GET /@<slug>/qr.png`) — open those directly in a browser.

## Regenerating

Whenever the API changes, regenerate both files from the actual code (run from the project root,
with the venv active and a database migrated — schema generation imports every view):

```bash
python manage.py spectacular --file docs/postman/openapi.yaml --format openapi
npx --yes openapi-to-postmanv2 -s docs/postman/openapi.yaml -o docs/postman/DBC_Backend.postman_collection.json -p
python3 docs/postman/patch_collection.py
```

The `npx` step overwrites the `baseUrl`/`bearerToken` variables, the collection description, and the
login/register auto-auth test scripts with the converter's plain defaults — `patch_collection.py`
(third command) reapplies all of that.
