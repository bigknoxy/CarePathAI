# Multi-stage build for CarePath.UI (Blazor Server)
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY ["CarePath.UI/CarePath.UI.csproj", "CarePath.UI/"]
COPY ["CarePath.Domain/CarePath.Domain.csproj", "CarePath.Domain/"]
RUN dotnet restore "CarePath.UI/CarePath.UI.csproj"

# Copy the rest of the source files
COPY . .
WORKDIR "/src/CarePath.UI"
RUN dotnet build "CarePath.UI.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "CarePath.UI.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Runtime stage
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .
EXPOSE 5001
ENV ASPNETCORE_URLS=http://+:5001
ENV ASPNETCORE_ENVIRONMENT=Production
ENTRYPOINT ["dotnet", "CarePath.UI.dll"]