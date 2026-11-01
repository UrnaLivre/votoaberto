plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Operator-owned upload key. Play App Signing owns the distribution key.
val uploadProperties = java.util.Properties()
val uploadPropertiesFile = rootProject.file("key.properties")
if (uploadPropertiesFile.exists()) {
    uploadPropertiesFile.inputStream().use { uploadProperties.load(it) }
}
fun uploadValue(name: String, environment: String): String? =
    System.getenv(environment)?.takeIf { it.isNotBlank() }
        ?: uploadProperties.getProperty(name)?.takeIf { it.isNotBlank() }
val uploadStore = uploadValue("storeFile", "ANDROID_UPLOAD_STORE_FILE")
val uploadStorePassword = uploadValue("storePassword", "ANDROID_UPLOAD_STORE_PASSWORD")
val uploadAlias = uploadValue("keyAlias", "ANDROID_UPLOAD_KEY_ALIAS")
val uploadKeyPassword = uploadValue("keyPassword", "ANDROID_UPLOAD_KEY_PASSWORD")
val hasUploadKey = listOf(uploadStore, uploadStorePassword, uploadAlias, uploadKeyPassword).all { it != null }

android {
    namespace = "br.com.urnalivre.votoaberto"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "br.com.urnalivre.votoaberto"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        // Play requirement checked for M7 (2026-11-01); recheck before M8 upload.
        targetSdk = 36
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (hasUploadKey) {
            create("upload") {
                storeFile = rootProject.file(uploadStore!!)
                storePassword = uploadStorePassword
                keyAlias = uploadAlias
                keyPassword = uploadKeyPassword
            }
        }
    }
    buildTypes {
        release {
            if (hasUploadKey) signingConfig = signingConfigs.getByName("upload")
        }
    }
}

gradle.taskGraph.whenReady {
    if (allTasks.any { it.project == project && it.name.contains("Release") } && !hasUploadKey) {
        throw GradleException("Release requires an operator-controlled upload key; see docs/NATIVE_RELEASES.md")
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
